from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def api_schema_view(request):
    return JsonResponse(
        {
            "title": "Movie Platform API",
            "version": "1.0.0",
            "description": "API for movies, genres, comments, ratings, and subscriptions.",
            "auth": {
                "register": "/api/auth/register/",
                "login": "/api/auth/login/",
                "logout": "/api/auth/logout/",
            },
            "resources": {
                "genres": "/api/genres/",
                "movies": "/api/movies/",
                "comments": "/api/comments/",
                "ratings": "/api/ratings/",
                "subscribers": "/api/subscribers/",
            },
        }
    )


urlpatterns = [
    path("", include("main.web_urls")),
    path("admin/", admin.site.urls),
    path("api/schema/", api_schema_view, name="api-schema"),
    path("api/", include("main.urls")),
]
