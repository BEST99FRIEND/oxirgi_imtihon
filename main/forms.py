from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Comment, Genre, Movie

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ("name", "description")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ("title", "description", "release_date", "duration_minutes", "genre")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "release_date": forms.DateInput(attrs={"type": "date"}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Film haqida fikringizni yozing...",
                }
            ),
        }
