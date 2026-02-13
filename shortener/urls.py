from django.urls import path
from . import views

# Create your tests here.
urlpatterns = [
    path("register/", views.register, name="register"),
]
