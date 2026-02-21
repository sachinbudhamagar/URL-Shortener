from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.db.models import F, Sum, Count, Q
from datetime import timedelta
from django.utils import timezone
from django.core.paginator import Paginator

from .forms import UserRegisterForm
from .models import URL, Click
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
        clicked_at=timezone.now(),
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        referrer=request.META.get("HTTP_REFERER", ""),
    )

    # Redirect to original URL (302 = temporary redirect)
    return redirect(url_obj.original_url)


def get_client_ip(request):
    """Extract client IP address from request headers"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def delete_url(request, short_code):
    url_obj = get_object_or_404(URL, short_code=short_code)

    # Verify ownership
    if url_obj.user != request.user:
        return HttpResponseForbidden("You dotn't own this  URL.")

    if request.method == "POST":
        url_obj.delete()  # Remove from database
        messages.success(request, "URL deleted successfully!")
        return redirect("dashboard")

    # Show confirmation page
    return render(request, "shortener/delete_confirm.html", {"url": url_obj})


@login_required
def analytics(request):
    user_urls = request.user.urls.all()

    # Overall statistics
    total_urls = user_urls.count()
    total_clicks = user_urls.aggregate(Sum("click_count"))["click_count__sum"] or 0

    # Most clicked URL
    most_clicked = user_urls.order_by("click_count").first()

    # Most clicked URL (excluding zero clicks)
    least_clicked = user_urls.filter(click_count__gt=0).order_by("click_count").first()

    # Recent activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_clicks = Click.objects.filter(
        url__user=request.user, clicked_at__gte=week_ago
    ).count()

    # Clicks per day (last 7 days)
    daily_clicks = []
    for i in range(7):
        day = timezone.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0)
        day_end = day.replace(hour=23, minute=59, second=59)

        count = Click.objects.filter(
            url__user=request.user, clicked_at__gte=day_start, clicked_at__lte=day_end
        ).count()

        daily_clicks.append({"date": day.strftime("%b %d"), "count": count})

    daily_clicks.reverse()  # Oldest to newest

    # Top 5 URLs by clicks
    top_urls = user_urls.order_by("-click_count")[:5]

    context = {
        "total_urls": total_urls,
        "total_clicks": total_clicks,
        "most_clicked": most_clicked,
        "least_clicked": least_clicked,
        "recent_clicks": recent_clicks,
        "daily_clicks": daily_clicks,
        "top_urls": top_urls,
    }

    return render(request, "shortener/analytics.html", context)


@login_required
def url_detail_analytics(request, short_code):
    """Detailed analytics for specific URL"""
    url_obj = get_object_or_404(URL, short_code=short_code)

    # Verify ownership
    if url_obj.user != request.user:
        return HttpResponseForbidden("You don't own this URL.")

    # Get all clicks for this URL
    all_clicks = url_obj.clicks.all().order_by("-clicked_at")

    # Unique visitors (by IP)
    unique_ips = url_obj.clicks.values("ip_address").distinct().count()

    # Top referrers
    top_referrers = (
        url_obj.clicks.values("referrer")
        .annotate(count=Count("id"))
        .order_by("-count")
        .exclude(referrer="")[:5]
    )

    # Browser/Device breakdown (simplified)
    user_agents = (
        url_obj.clicks.values("user_agent")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    # Geographic data (basic - IP-based would need external service)
    # For now, just show unique IPs

    # Clicks y hour (24-hour breakdown)
    hourly_clicks = []
    for hour in range(24):
        count = url_obj.clicks.filter(clicked_at__hour=hour).count()
        hourly_clicks.append({"hour": f"{hour:02d}:00", "count": count})

    context = {
        "url": url_obj,
        "total_clicks": url_obj.click_count,
        "unique_visitors": unique_ips,
        "recent_clicks": all_clicks[:20],  # Last 20 clicks
        "top_referrers": top_referrers,
        "hourly_clicks": hourly_clicks,
    }

    return render(request, "shortener/url_detail.html", context)


def home(request):
    """Landing page with URL shortening form"""
    if request.method == "POST":
        # Allow anonymus URL shortening
        form = URLForm(request.POST)
        if form.is_valid():
            url_obj = form.save(commit=False)

            # If loggin in, assign user
            if request.user.is_authenticated:
                url_obj_user = request.user
            # If anonymus, leave user as None (need to modify model)

            # Generate  short code
            url_obj.short_code = generate_random_code()
            url_obj.save()

            short_url = request.build_absolute_url("/") + url_obj.short_code

            return render(
                request,
                "shortener/home.html",
                {
                    "form": URLForm(),
                    "short_url": short_url,
                    "show_signup_prompt": not request.user.is_authenticated,
                },
            )
        else:
            form = URLForm()

        return render(request, "shortener/home.html", {"form": form})
