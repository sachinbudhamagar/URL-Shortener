from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# Create your tests here.
urlpatterns = [
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="shortener/login.html",
        ),
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("analytics/", views.analytics, name="analytics"),
    path("create/", views.create_url, name="create_url"),
    path("delete/<str:short_code>/", views.delete_url, name="delete_url"),
    path("edit/<str:short_code>/", views.edit_url, name="edit_url"),
    path(
        "url/<str:short_code>/analytics/",
        views.url_detail_analytics,
        name="url_detail_analytics",
    ),
    path("qr/<str:short_code>/", views.generate_qr_view, name="generate_qr"),
    path("qr/<str:short_code>/download/", views.download_qr, name="download_qr"),
    path(
        "url/<str:check_code>/download/",
        views.download_qr,
        name="download_qr",
    ),
    path(
        "url/<str:check_code>/<str:code>/",
        views.check_code_availability,
        name="check_code",
    ),
    path("<str:short_code>/", views.redirect_url, name="redirect"),
    path("", views.home, name="home"),
]
