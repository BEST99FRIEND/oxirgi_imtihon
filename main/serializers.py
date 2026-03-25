from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Comment, Genre, Movie, MovieSubscriber, Rating

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "password_confirm")
        read_only_fields = ("id",)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name", "description", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

class MovieSerializer(serializers.ModelSerializer):
    genre_name = serializers.CharField(source="genre.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    likes_count = serializers.SerializerMethodField()
    dislikes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = (
            "id",
            "title",
            "description",
            "release_date",
            "duration_minutes",
            "genre",
            "genre_name",
            "created_by",
            "created_by_username",
            "likes_count",
            "dislikes_count",
            "comments_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_by",
            "created_by_username",
            "likes_count",
            "dislikes_count",
            "comments_count",
            "created_at",
            "updated_at",
        )

    def get_likes_count(self, obj):
        value = getattr(obj, "likes_count", None)
        return value if value is not None else obj.ratings.filter(value=Rating.LIKE).count()

    def get_dislikes_count(self, obj):
        value = getattr(obj, "dislikes_count", None)
        return value if value is not None else obj.ratings.filter(value=Rating.DISLIKE).count()

    def get_comments_count(self, obj):
        value = getattr(obj, "comments_count", None)
        return value if value is not None else obj.comments.count()

class CommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "movie",
            "user",
            "user_username",
            "text",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "user_username", "created_at", "updated_at")

class RatingSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Rating
        fields = (
            "id",
            "movie",
            "user",
            "user_username",
            "value",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "user_username", "created_at", "updated_at")

    def validate(self, attrs):
        request = self.context.get("request")
        user = attrs.get("user") or (request.user if request else None)
        movie = attrs.get("movie") or getattr(self.instance, "movie", None)

        if self.instance is None and user and movie:
            if Rating.objects.filter(user=user, movie=movie).exists():
                raise serializers.ValidationError("You already rated this movie.")

        return attrs

class MovieSubscriberSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = MovieSubscriber
        fields = (
            "id",
            "user",
            "user_username",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "user_username", "created_at", "updated_at")

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        if self.instance is None and user and MovieSubscriber.objects.filter(user=user).exists():
            raise serializers.ValidationError(
                "Subscription already exists for this user. Use update endpoint."
            )
        return attrs
