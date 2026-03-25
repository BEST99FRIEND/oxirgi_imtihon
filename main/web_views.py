import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import CommentForm, GenreForm, MovieForm, RegisterForm
from .models import Comment, Genre, Movie, MovieSubscriber, Rating


class RegisterPageView(CreateView):
    template_name = "auth/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Profil muvaffaqiyatli yaratildi.")
        return response


class CustomLoginView(LoginView):
    template_name = "auth/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("home")


class HomePageView(TemplateView):
    template_name = "home.html"

    def _build_rating_trend(self):
        start_date = timezone.localdate() - timedelta(days=13)

        rows = (
            Rating.objects.filter(created_at__date__gte=start_date)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(
                likes=Count("id", filter=Q(value=Rating.LIKE)),
                dislikes=Count("id", filter=Q(value=Rating.DISLIKE)),
            )
            .order_by("day")
        )

        mapped = {
            row["day"]: {
                "likes": row["likes"],
                "dislikes": row["dislikes"],
            }
            for row in rows
        }

        labels = []
        likes = []
        dislikes = []

        for offset in range(14):
            current_day = start_date + timedelta(days=offset)
            labels.append(current_day.strftime("%m-%d"))
            day_stats = mapped.get(current_day, {"likes": 0, "dislikes": 0})
            likes.append(day_stats["likes"])
            dislikes.append(day_stats["dislikes"])

        return labels, likes, dislikes

    def _build_top_genres(self):
        rows = (
            Genre.objects.annotate(movie_count=Count("movies", distinct=True))
            .filter(movie_count__gt=0)
            .order_by("-movie_count", "name")[:8]
        )

        labels = [genre.name for genre in rows]
        movie_counts = [genre.movie_count for genre in rows]
        return labels, movie_counts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = {
            "movies": Movie.objects.count(),
            "genres": Genre.objects.count(),
            "comments": Comment.objects.count(),
            "ratings": Rating.objects.count(),
        }
        context["latest_movies"] = (
            Movie.objects.select_related("genre", "created_by")
            .annotate(
                likes_count=Count("ratings", filter=Q(ratings__value=Rating.LIKE)),
                dislikes_count=Count("ratings", filter=Q(ratings__value=Rating.DISLIKE)),
            )
            .order_by("-created_at")[:6]
        )

        rating_labels, rating_likes, rating_dislikes = self._build_rating_trend()
        genre_labels, genre_movie_counts = self._build_top_genres()

        context["rating_trend_labels"] = json.dumps(rating_labels)
        context["rating_trend_likes"] = json.dumps(rating_likes)
        context["rating_trend_dislikes"] = json.dumps(rating_dislikes)
        context["top_genre_labels"] = json.dumps(genre_labels)
        context["top_genre_movie_counts"] = json.dumps(genre_movie_counts)

        if self.request.user.is_authenticated:
            context["subscription"] = MovieSubscriber.objects.filter(
                user=self.request.user,
                is_active=True,
            ).exists()
        return context


class MovieListView(ListView):
    template_name = "movies/movie_list.html"
    model = Movie
    context_object_name = "movies"
    paginate_by = 8

    def get_queryset(self):
        queryset = (
            Movie.objects.select_related("genre", "created_by")
            .annotate(
                likes_count=Count("ratings", filter=Q(ratings__value=Rating.LIKE)),
                dislikes_count=Count("ratings", filter=Q(ratings__value=Rating.DISLIKE)),
                comments_count=Count("comments", distinct=True),
            )
            .all()
        )

        search = self.request.GET.get("search")
        genre = self.request.GET.get("genre")
        min_duration = self.request.GET.get("min_duration")
        max_duration = self.request.GET.get("max_duration")
        ordering = self.request.GET.get("ordering", "-created_at")

        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        if genre and genre.isdigit():
            queryset = queryset.filter(genre_id=int(genre))
        if min_duration and min_duration.isdigit():
            queryset = queryset.filter(duration_minutes__gte=int(min_duration))
        if max_duration and max_duration.isdigit():
            queryset = queryset.filter(duration_minutes__lte=int(max_duration))

        allowed_ordering = {
            "title",
            "-title",
            "release_date",
            "-release_date",
            "created_at",
            "-created_at",
            "duration_minutes",
            "-duration_minutes",
        }
        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["genres"] = Genre.objects.all()
        context["filters"] = {
            "search": self.request.GET.get("search", ""),
            "genre": self.request.GET.get("genre", ""),
            "min_duration": self.request.GET.get("min_duration", ""),
            "max_duration": self.request.GET.get("max_duration", ""),
            "ordering": self.request.GET.get("ordering", "-created_at"),
        }
        return context


class MovieDetailView(DetailView):
    template_name = "movies/movie_detail.html"
    model = Movie
    context_object_name = "movie"

    def get_queryset(self):
        return Movie.objects.select_related("genre", "created_by").annotate(
            likes_count=Count("ratings", filter=Q(ratings__value=Rating.LIKE)),
            dislikes_count=Count("ratings", filter=Q(ratings__value=Rating.DISLIKE)),
            comments_count=Count("comments", distinct=True),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movie = self.object
        context["comments"] = movie.comments.select_related("user").all()
        context["comment_form"] = CommentForm()
        context["can_edit"] = self.request.user.is_authenticated and (
            self.request.user.is_staff or movie.created_by_id == self.request.user.id
        )
        context["user_rating"] = None
        if self.request.user.is_authenticated:
            context["user_rating"] = Rating.objects.filter(movie=movie, user=self.request.user).first()
        return context


class OwnerOrStaffMovieMixin(UserPassesTestMixin):
    def test_func(self):
        movie = self.get_object()
        return self.request.user.is_staff or movie.created_by_id == self.request.user.id


class MovieCreateView(LoginRequiredMixin, CreateView):
    template_name = "movies/movie_form.html"
    form_class = MovieForm
    success_url = reverse_lazy("web-movie-list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Film muvaffaqiyatli yaratildi.")
        return super().form_valid(form)


class MovieUpdateView(LoginRequiredMixin, OwnerOrStaffMovieMixin, UpdateView):
    template_name = "movies/movie_form.html"
    model = Movie
    form_class = MovieForm

    def get_success_url(self):
        return reverse_lazy("web-movie-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Film yangilandi.")
        return super().form_valid(form)


class MovieDeleteView(LoginRequiredMixin, OwnerOrStaffMovieMixin, DeleteView):
    template_name = "movies/movie_confirm_delete.html"
    model = Movie
    success_url = reverse_lazy("web-movie-list")

    def form_valid(self, form):
        messages.success(self.request, "Film ochirildi.")
        return super().form_valid(form)


class GenreListView(ListView):
    template_name = "genres/genre_list.html"
    model = Genre
    context_object_name = "genres"


class GenreCreateView(LoginRequiredMixin, CreateView):
    template_name = "genres/genre_form.html"
    form_class = GenreForm
    success_url = reverse_lazy("web-genre-list")

    def form_valid(self, form):
        messages.success(self.request, "Janr yaratildi.")
        return super().form_valid(form)


class GenreUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "genres/genre_form.html"
    form_class = GenreForm
    model = Genre
    success_url = reverse_lazy("web-genre-list")

    def form_valid(self, form):
        messages.success(self.request, "Janr yangilandi.")
        return super().form_valid(form)


@login_required
def add_comment(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.movie = movie
            comment.user = request.user
            comment.save()
            messages.success(request, "Izoh qoshildi.")
        else:
            messages.error(request, "Izoh formati notogri.")
    return redirect("web-movie-detail", pk=movie.pk)


@login_required
def set_rating(request, pk, action):
    movie = get_object_or_404(Movie, pk=pk)

    if request.method != "POST":
        return redirect("web-movie-detail", pk=movie.pk)

    if action == "like":
        value = Rating.LIKE
    elif action == "dislike":
        value = Rating.DISLIKE
    else:
        messages.error(request, "Noto'g'ri rating turi.")
        return redirect("web-movie-detail", pk=movie.pk)

    rating, created = Rating.objects.get_or_create(
        movie=movie,
        user=request.user,
        defaults={"value": value},
    )
    if not created:
        rating.value = value
        rating.save(update_fields=["value", "updated_at"])

    messages.success(request, "Baholash saqlandi.")
    return redirect("web-movie-detail", pk=movie.pk)


@login_required
def toggle_subscription(request):
    if request.method != "POST":
        return redirect("home")

    subscription, _ = MovieSubscriber.objects.get_or_create(user=request.user)
    subscription.is_active = not subscription.is_active
    subscription.save(update_fields=["is_active", "updated_at"])

    if subscription.is_active:
        messages.success(request, "Email xabarnoma yoqildi.")
    else:
        messages.info(request, "Email xabarnoma o'chirildi.")

    return redirect("home")
