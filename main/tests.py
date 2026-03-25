from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from .models import Comment, Genre, Movie, MovieSubscriber, Rating

User = get_user_model()

class AuthenticationAPITests(APITestCase):
    def test_user_can_register(self):
        payload = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password": "StrongPass123",
            "password_confirm": "StrongPass123",
        }
        response = self.client.post(reverse("register"), payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["username"], payload["username"])

    def test_user_can_login(self):
        user = User.objects.create_user(
            username="existing_user",
            email="existing_user@example.com",
            password="StrongPass123",
        )
        Token.objects.get_or_create(user=user)

        payload = {"username": "existing_user", "password": "StrongPass123"}
        response = self.client.post(reverse("login"), payload, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["id"], user.id)

    def test_openapi_schema_endpoint_is_available(self):
        response = self.client.get(reverse("api-schema"))

        self.assertEqual(response.status_code, 200)

@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class MoviePlatformAPITests(APITestCase):
    def setUp(self):
        self.user_1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="StrongPass123",
        )
        self.user_2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="StrongPass123",
        )
        self.token_1 = Token.objects.create(user=self.user_1)
        self.token_2 = Token.objects.create(user=self.user_2)

        self.genre_action = Genre.objects.create(name="Action")
        self.genre_drama = Genre.objects.create(name="Drama")
        self.movie = Movie.objects.create(
            title="Starter Movie",
            description="Base movie for tests.",
            release_date="2024-01-01",
            duration_minutes=120,
            genre=self.genre_action,
            created_by=self.user_1,
        )

    def authenticate(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def test_user_must_be_authenticated_to_create_movie(self):
        payload = {
            "title": "Unauthorized Movie",
            "description": "Should fail",
            "release_date": "2025-01-01",
            "duration_minutes": 110,
            "genre": self.genre_action.id,
        }
        response = self.client.post(reverse("movie-list"), payload, format="json")

        self.assertEqual(response.status_code, 401)

    def test_create_movie_sends_email_to_active_subscribers(self):
        MovieSubscriber.objects.create(user=self.user_2, is_active=True)
        self.authenticate(self.token_1.key)

        payload = {
            "title": "New Movie",
            "description": "Notification test",
            "release_date": "2026-03-01",
            "duration_minutes": 123,
            "genre": self.genre_action.id,
        }
        response = self.client.post(reverse("movie-list"), payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["created_by"], self.user_1.id)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user_2.email, mail.outbox[0].to)

    def test_movie_filter_search_ordering_and_pagination(self):
        for index in range(1, 8):
            Movie.objects.create(
                title=f"Action {index}",
                description="Action movie",
                release_date="2025-05-10",
                duration_minutes=90 + index,
                genre=self.genre_action,
                created_by=self.user_1,
            )

        Movie.objects.create(
            title="Drama Special",
            description="Drama movie",
            release_date="2025-05-10",
            duration_minutes=140,
            genre=self.genre_drama,
            created_by=self.user_1,
        )

        response = self.client.get(
            reverse("movie-list"),
            {
                "genre": self.genre_action.id,
                "release_year": "2025",
                "min_duration": "93",
                "search": "Action",
                "ordering": "title",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNone(response.data["next"])

        titles = [item["title"] for item in response.data["results"]]
        self.assertEqual(titles, sorted(titles))

    def test_only_comment_owner_can_update_comment(self):
        comment = Comment.objects.create(
            movie=self.movie,
            user=self.user_1,
            text="First comment",
        )

        self.authenticate(self.token_2.key)
        forbidden_response = self.client.patch(
            reverse("comment-detail", kwargs={"pk": comment.id}),
            {"text": "Trying to edit"},
            format="json",
        )
        self.assertEqual(forbidden_response.status_code, 403)

        self.authenticate(self.token_1.key)
        success_response = self.client.patch(
            reverse("comment-detail", kwargs={"pk": comment.id}),
            {"text": "Owner updated"},
            format="json",
        )
        self.assertEqual(success_response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.text, "Owner updated")

    def test_user_cannot_rate_same_movie_twice(self):
        self.authenticate(self.token_1.key)

        first_response = self.client.post(
            reverse("rating-list"),
            {"movie": self.movie.id, "value": Rating.LIKE},
            format="json",
        )
        second_response = self.client.post(
            reverse("rating-list"),
            {"movie": self.movie.id, "value": Rating.DISLIKE},
            format="json",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 400)

    def test_subscriber_list_returns_only_current_user_data(self):
        MovieSubscriber.objects.create(user=self.user_1, is_active=True)
        MovieSubscriber.objects.create(user=self.user_2, is_active=False)

        self.authenticate(self.token_1.key)
        response = self.client.get(reverse("subscriber-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["user"], self.user_1.id)

    def test_only_movie_owner_can_update_movie(self):
        self.authenticate(self.token_2.key)
        forbidden_response = self.client.patch(
            reverse("movie-detail", kwargs={"pk": self.movie.id}),
            {"title": "Hacked title"},
            format="json",
        )
        self.assertEqual(forbidden_response.status_code, 403)

        self.authenticate(self.token_1.key)
        success_response = self.client.patch(
            reverse("movie-detail", kwargs={"pk": self.movie.id}),
            {"title": "Updated by owner"},
            format="json",
        )
        self.assertEqual(success_response.status_code, 200)
        self.movie.refresh_from_db()
        self.assertEqual(self.movie.title, "Updated by owner")

    def test_subscriber_cannot_be_created_twice_for_same_user(self):
        self.authenticate(self.token_1.key)
        first_response = self.client.post(
            reverse("subscriber-list"),
            {"is_active": True},
            format="json",
        )
        second_response = self.client.post(
            reverse("subscriber-list"),
            {"is_active": False},
            format="json",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 400)

    def test_movie_detail_returns_correct_stats(self):
        Comment.objects.create(movie=self.movie, user=self.user_1, text="Great")
        Comment.objects.create(movie=self.movie, user=self.user_2, text="Nice")
        Rating.objects.create(movie=self.movie, user=self.user_1, value=Rating.LIKE)
        Rating.objects.create(movie=self.movie, user=self.user_2, value=Rating.DISLIKE)

        response = self.client.get(reverse("movie-detail", kwargs={"pk": self.movie.id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["likes_count"], 1)
        self.assertEqual(response.data["dislikes_count"], 1)
        self.assertEqual(response.data["comments_count"], 2)

class TemplateSmokeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="template_user",
            email="template@example.com",
            password="StrongPass123",
        )
        self.genre = Genre.objects.create(name="Sci-Fi")
        self.movie = Movie.objects.create(
            title="Template Movie",
            description="Template detail test",
            release_date="2025-10-10",
            duration_minutes=130,
            genre=self.genre,
            created_by=self.user,
        )

    def test_home_template_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MovieVerse")
        self.assertContains(response, "ratingTrendChart")
        self.assertContains(response, "topGenresChart")

    def test_movie_list_template_page_loads(self):
        response = self.client.get(reverse("web-movie-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Template Movie")

    def test_movie_detail_template_page_loads(self):
        response = self.client.get(reverse("web-movie-detail", kwargs={"pk": self.movie.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Template detail test")

    def test_movie_create_template_requires_login(self):
        response = self.client.get(reverse("web-movie-create"))
        self.assertEqual(response.status_code, 302)

