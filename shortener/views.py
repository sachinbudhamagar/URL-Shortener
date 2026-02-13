from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required


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
def logout_view(requst):
    logout(requst)
    messages.info(requst, "You have been logged out.")
    return redirect("home")
