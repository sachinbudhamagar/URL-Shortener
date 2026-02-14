from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from .models import URL
from .forms import URLForm
from .utils import generate_short_code, generate_random_code


# Create your views here.
def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()  # Django automatically hashes password
            username = form.cleaned_data.get("username")
            messages.success(
                request, f"Account created for {username}! You can now log in."
            )
            return redirect("login")  # Redirect to login page

        else:
            form = UserRegisterForm()  # Empty form for GET request

        return render(request, "shortener/register.html", {"form": form})


@login_required  # Requires user to be logged in
def dashboard(request):
    # Get only URLs belonging to current user
    user_urls = request.user.urls.all()  # Uses related_name from model
    return render(request, "shortener/dashboard.html", {"urls": user_urls})


@login_required
def edit_url(request, short_code):
    # Get URL object or 404 if not found
    url_obj = get_object_or_404(URL, short_code=short_code)

    # Check ownership
    if url_obj.user != request.user:
        return HttpResponseForbidden("You don't have permission to edit this URL.")


@login_required
def logout_view(requst):
    logout(requst)
    messages.info(requst, "You have been logged out.")
    return redirect("home")


@login_required
def create_url(request):
    if request.method == "POST":
        form = URLForm(request.POST)
        if form.is_valid():
            # Save but don't commit to database yet
            url_obj = form.save(commit=False)
            url_obj.user = request.user  # Set owner

            # Check for custom code
            custom_code = form.cleaned_data.get("custom_short_code")
            if custom_code:
                url_obj.short_code = custom_code
                url_obj.custom_code = True
            else:
                # Generate random code (we'll use ID-based after save)
                url_obj.short_code = generate_random_code()

            url_obj.save()  # Save to database

            # If using ID-based encoding, update short_code
            # url_obj.short_code = generate_short_code(url_obj.id)
            # url_obj.save()

            messages.success(request, "URL shortened successfully!")
            return render(
                request,
                "shortener/create_url.html",
                {
                    "form": URLForm(),  # Fresh form
                    "short_url": request.build_absolute_uri("/") + url_obj.short_code,
                },
            )

        else:
            form = URLForm()

        return render(request, "shortener/create_url.html", {"form": form})
