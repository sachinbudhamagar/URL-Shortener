from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from .models import URL


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
