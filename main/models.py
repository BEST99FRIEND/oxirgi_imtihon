from django.conf import settings
from django.db import models

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Genre(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

class Movie(TimeStampedModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    release_date = models.DateField()
    duration_minutes = models.PositiveIntegerField()
    genre = models.ForeignKey(Genre, related_name="movies", on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="movies",
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title

class Comment(TimeStampedModel):
    movie = models.ForeignKey(Movie, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="comments",
        on_delete=models.CASCADE,
    )
    text = models.TextField()

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Comment by {self.user} on {self.movie}"

class Rating(TimeStampedModel):
    LIKE = 1
    DISLIKE = -1
    RATING_CHOICES = (
        (LIKE, "Like"),
        (DISLIKE, "Dislike"),
    )

    movie = models.ForeignKey(Movie, related_name="ratings", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="ratings",
        on_delete=models.CASCADE,
    )
    value = models.SmallIntegerField(choices=RATING_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("movie", "user"),
                name="unique_user_movie_rating",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} rated {self.movie}: {self.value}"

class MovieSubscriber(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="movie_subscription",
        on_delete=models.CASCADE,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.user} subscription: {self.is_active}"
