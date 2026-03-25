from django.urls import path

from .web_views import (
    CustomLoginView,
    CustomLogoutView,
    GenreCreateView,
    GenreListView,
    GenreUpdateView,
    HomePageView,
    MovieCreateView,
    MovieDeleteView,
    MovieDetailView,
    MovieListView,
    MovieUpdateView,
    RegisterPageView,
    add_comment,
    set_rating,
    toggle_subscription,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("accounts/register/", RegisterPageView.as_view(), name="web-register"),
    path("accounts/login/", CustomLoginView.as_view(), name="web-login"),
    path("accounts/logout/", CustomLogoutView.as_view(), name="web-logout"),
    path("movies/", MovieListView.as_view(), name="web-movie-list"),
    path("movies/create/", MovieCreateView.as_view(), name="web-movie-create"),
    path("movies/<int:pk>/", MovieDetailView.as_view(), name="web-movie-detail"),
    path("movies/<int:pk>/edit/", MovieUpdateView.as_view(), name="web-movie-edit"),
    path("movies/<int:pk>/delete/", MovieDeleteView.as_view(), name="web-movie-delete"),
    path("movies/<int:pk>/comment/", add_comment, name="web-add-comment"),
    path("movies/<int:pk>/rate/<str:action>/", set_rating, name="web-set-rating"),
    path("genres/", GenreListView.as_view(), name="web-genre-list"),
    path("genres/create/", GenreCreateView.as_view(), name="web-genre-create"),
    path("genres/<int:pk>/edit/", GenreUpdateView.as_view(), name="web-genre-edit"),
    path("subscription/toggle/", toggle_subscription, name="web-toggle-subscription"),
]
