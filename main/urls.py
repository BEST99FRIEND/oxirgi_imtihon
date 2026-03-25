from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CommentViewSet,
    GenreViewSet,
    LoginAPIView,
    LogoutAPIView,
    MovieSubscriberViewSet,
    MovieViewSet,
    RatingViewSet,
    RegisterAPIView,
)

router = DefaultRouter()
router.register("genres", GenreViewSet, basename="genre")
router.register("movies", MovieViewSet, basename="movie")
router.register("comments", CommentViewSet, basename="comment")
router.register("ratings", RatingViewSet, basename="rating")
router.register("subscribers", MovieSubscriberViewSet, basename="subscriber")

urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view(), name="register"),
    path("auth/login/", LoginAPIView.as_view(), name="login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="logout"),
    path("auth/", include("rest_framework.urls")),
    path("", include(router.urls)),
]
