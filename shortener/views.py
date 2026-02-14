from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden
from .models import URL, Click
from .forms import URLForm
from .utils import generate_short_code, generate_random_code
from django.db.models import F
from django.core.paginator import Paginator


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
    # Get only URLs belonging to current user, ordered by newest first
    url_list = request.user.urls.all()  # Uses related_name from model

    # Pagination (10 URLs per page)
    pagination = Paginator(url_list, 10)
    page_number = request.GET.get("page")
    urls = pagination.get_page(page_number)

    # Calculate total stats
    total_clicks = sum(url.click_count for url in url_list)
    total_urls = url_list.count()

    context = {
        "urls": urls,
        "total_clicks": total_clicks,
        "total_urls": total_urls,
    }
    return render(request, "shortener/dashboard.html", context)


@login_required
def edit_url(request, short_code):
    # Get URL object or 404 if not found
    url_obj = get_object_or_404(URL, short_code=short_code)

    # Check/Verify ownership
    if url_obj.user != request.user:
        return HttpResponseForbidden("You don't own this URL.")

    if request.method == "POST":
        if request.method == "POST":
            form = URLForm(request.POST, instance=url_obj)
            if form.is_valid():
                form.save()
                messages.success(request, "URL updated successfully!")
                return redirect("dashboard")
    else:
        # Pre-fil form with existing data
        form = URLForm(instance=url_obj)

    return render(request, "shortener/edit_url.html", {"form": form, "url": url_obj})


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


# Redirection Logic
def redirect_url(request, short_code):
    """Redirect short code to original URL"""
    # Get URL object or show 404
    url_obj = get_object_or_404(URL, short_code=short_code)

    # Check if expired
    if url_obj.is_expired():
        return render(request, "shortener/expired.html", {"url": url_obj})

    # Increment click count (F() prevents race conditions)
    url_obj.click_count = F("click_count") + 1
    url_obj.save()
    url_obj.refresh_from_db()  # Get updated count

    # Optional: Log detailed click data
    Click.objects.create(
        url=url_obj,
        ip_address=request.META.get("HTTP_USER_AGENT", "")[:300],
        referrer=request.META.get("HTTP_REFERER", ""),
    )

    # Redirect to original URL (302 = temporary redirect)
    return redirect(url_obj.original_url)


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
