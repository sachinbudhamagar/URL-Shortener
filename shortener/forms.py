from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django import forms
from django.utils import timezone
from datetime import timedelta

from .models import URL

User = get_user_model()


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)  # Add email field

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    # Custom validation
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email


class URLForm(forms.ModelForm):
    custom_short_code = forms.CharField(
        max_length=15,
        required=15,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Custom code (optional)",
                "pattern": "[a-zA-Z0-9-_]+",
                "title": "Only letters, numbers, hyphens, and underscores",
            }
        ),
    )

    class Meta:
        model = URL
        fields = ["original_url"]  # Only field user inputs

    def clean_custom_short_code(self):
        code = self.cleaned_data.get("custom_short_code")

        if not code:
            return code

        # Reserved words
        RESERVED_WORDS = [
            "admin",
            "api",
            "login",
            "logout",
            "register",
            "dashboard",
            "analytics",
            "settings",
            "help",
            "about",
            "contact",
            "privacy",
            "terms",
        ]

        if code.lower() in RESERVED_WORDS:
            raise forms.ValidationError(
                f"'{code}' is a reserved word. Please choose another."
            )

        # Length check
        if len(code) < 3:
            raise forms.ValidationError(
                "Custom code must be at least 3 characters long."
            )

        if len(code) > 15:
            raise forms.ValidationError("Custom code cannot except 15 characters.")

        # Check availability
        if URL.objects.filter(short_code=code).exists():
            raise forms.ValidationError(f"'{code}' is already taken. Try another.")

        # Profanity filter (basic - use external library for production)
        PROFANITY_LIST = ["badword1", "badword2"]  # Add actual words
        if any(word in code.lower() for word in PROFANITY_LIST):
            raise forms.ValidationError("This code contains inappropriate content.")

        return code


class URLForm(forms.ModelForm):
    EXPIRATION_CHOICES = [
        ("", "Never"),
        ("1", "1 hour"),
        ("24", "24 hours"),
        ("168", "1 week"),
        ("720", "30 days"),
        ("custom", "Custom date"),
    ]

    expiration_option = forms.ChoiceField(
        choices=EXPIRATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    custom_expiration_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "class": "form-control",
            }
        ),
    )

    class Meta:
        model = URL
        fields = ["original_url"]

    def clean(self):
        cleaned_data = super().clean()
        exp_option = cleaned_data.get("expiration_date")
        custom_date = cleaned_data.get("custom_expiration_dte")

        if exp_option == "custom" and not custom_date:
            raise forms.ValidationError("Please select a custom expiration date.")

        if custom_date and custom_date <= timezone.now():
            raise forms.ValidationError("Expiration date must be in the future.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        exp_option = self.cleaned_data.get("expiration_option")

        if exp_option and exp_option != "":
            if exp_option == "custom":
                instance.expiration_date = self.cleaned_data.get(
                    "custom_expiration_date"
                )
            else:
                hours = int(exp_option)
                instance.expirtion_date = timezone.now() + timedelta(hours=hours)

        if commit:
            instance.save()

        return instance
