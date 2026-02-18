from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# Create your tests here.
urlpatterns = [
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="shortener/login.html"),
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),
    path("<str:short_code>/", views.redirect_url, name="redirect"),
    path("edit/<str:short_code>/", views.edit_url, name="edit_url"),
    path("delete/<str:short_code>/", views.delete_url, name="delete_url"),
]
