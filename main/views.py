from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Comment, Genre, Movie, MovieSubscriber, Rating
from .permissions import IsOwnerOrCreatorOrReadOnly
from .serializers import (
    CommentSerializer,
    GenreSerializer,
    MovieSerializer,
    MovieSubscriberSerializer,
    RatingSerializer,
    UserRegisterSerializer,
    UserSerializer,
)

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {"user": UserSerializer(user).data, "token": token.key},
            status=status.HTTP_201_CREATED,
        )

class LoginAPIView(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)

        return Response({"token": token.key, "user": UserSerializer(user).data})

class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)

class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ("name", "description")
    ordering_fields = ("name", "created_at")

class MovieViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrCreatorOrReadOnly]
    search_fields = ("title", "description", "genre__name")
    ordering_fields = ("title", "release_date", "duration_minutes", "created_at")

    def get_queryset(self):
        queryset = (
            Movie.objects.select_related("genre", "created_by")
            .annotate(
                likes_count=Count("ratings", filter=Q(ratings__value=Rating.LIKE), distinct=True),
                dislikes_count=Count("ratings", filter=Q(ratings__value=Rating.DISLIKE), distinct=True),
                comments_count=Count("comments", distinct=True),
            )
            .all()
        )

        genre = self.request.query_params.get("genre")
        release_year = self.request.query_params.get("release_year")
        created_by = self.request.query_params.get("created_by")
        min_duration = self.request.query_params.get("min_duration")
        max_duration = self.request.query_params.get("max_duration")

        if genre:
            queryset = queryset.filter(genre_id=genre)
        if release_year and release_year.isdigit():
            queryset = queryset.filter(release_date__year=int(release_year))
        if created_by and created_by.isdigit():
            queryset = queryset.filter(created_by_id=int(created_by))
        if min_duration and min_duration.isdigit():
            queryset = queryset.filter(duration_minutes__gte=int(min_duration))
        if max_duration and max_duration.isdigit():
            queryset = queryset.filter(duration_minutes__lte=int(max_duration))

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related("movie", "user").all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrCreatorOrReadOnly]
    search_fields = ("text", "movie__title", "user__username")
    ordering_fields = ("created_at",)

    def get_queryset(self):
        queryset = super().get_queryset()
        movie = self.request.query_params.get("movie")
        if movie and movie.isdigit():
            queryset = queryset.filter(movie_id=int(movie))
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.select_related("movie", "user").all()
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrCreatorOrReadOnly]
    search_fields = ("movie__title", "user__username")
    ordering_fields = ("value", "created_at")

    def get_queryset(self):
        queryset = super().get_queryset()
        movie = self.request.query_params.get("movie")
        value = self.request.query_params.get("value")
        if movie and movie.isdigit():
            queryset = queryset.filter(movie_id=int(movie))
        if value in {"1", "-1"}:
            queryset = queryset.filter(value=int(value))
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MovieSubscriberViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSubscriberSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrCreatorOrReadOnly]
    search_fields = ("user__username", "user__email")
    ordering_fields = ("created_at", "is_active")

    def get_queryset(self):
        queryset = MovieSubscriber.objects.select_related("user").all()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
