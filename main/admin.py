from django.contrib import admin
from .models import Comment, Genre, Movie, MovieSubscriber, Rating

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "genre", "release_date", "created_by")
    list_filter = ("genre", "release_date")
    search_fields = ("title", "description", "created_by__username")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "movie", "user", "created_at")
    search_fields = ("movie__title", "user__username", "text")

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("id", "movie", "user", "value", "created_at")
    list_filter = ("value",)
    search_fields = ("movie__title", "user__username")

@admin.register(MovieSubscriber)
class MovieSubscriberAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("user__username", "user__email")
