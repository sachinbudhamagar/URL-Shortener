from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from .models import URL


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
    class Meta:
        model = URL
        fields = ["original_url"]  # Only field user inputs
        widgets = {
            "original_url": forms.URLInput(
                attrs={
                    "placeholder": "Enter your long URL here....",
                    "class": "form-control",
                }
            )
        }

    # Optional: Custom short code field
    custom_short_code = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Custom code (optional)"}),
    )

    def clean_custom_short_code(self):
        code = self.cleaned_data.get("custom_short_code")
        if code:
            # Check if already exists
            if URL.objects.filter(short_code=code).exists():
                raise forms.ValidationError("This custom code is already taken.")
            # Only alphanumeric
            if not code.isalnum():
                raise forms.ValidationError("OOnly letters and numbers allowed.")
        return code
