from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone


# Model 1: URL - Stores shortened URLs
class URL(models.Model):
    # Fields
    orginal_urls = models.URLField(max_length=2000)  # Long URLs
    short_code = models.CharField(
        max_length=15, unique=True, db_index=True
    )  # Unique short code
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Auto-set on create
    updated_at = models.DateTimeField(auto_now=True)  # Auto-update on save
    click_count = models.IntegerField(default=0)  # Track total clicks

    # Relationship: Each URL belongs to one user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="urls"
    )
    # on_delete = CASCADE means: if user deleted, delete their URLs too
    # related_name = "urls" means: access user's URLs via user.urls.all()

    # Optional fields for bonus features
    custom_code = models.BooleanField(default=False)  # Track if custom
    expiration_date = models.DateTimeField(null=True, blank=True)  # Optional expiry

    class Meta:
        ordering = ["-created_at"]  # Newest first
        indexes = [
            models.Index(fields=["short_code"]),  # Fast lookups
        ]

    def __str__(self):
        return f"{self.short_code} -> {self.original_url[:50]}"

    def is_expired(self):
        if self.expiration_date:
            return timezone.now() > self.expiration_date
        return False


# Model 2: Click - Stores detailed click analytics (optional for Phase 5.3)
class Click(models.Model):
    # Relationship: Each click belongs to one URL
    url = models.ForeignKey(URL, on_delete=models.CASCADE, related_name="clicks")

    # Analytics fields
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)  # Browser info
    referrer = models.URLField(max_length=2000, blank=True)  # Where click came from

    class Meta:
        ordering = ["-clicked_at"]

    def __str__(self):
        return f"Click on {self.url.short_code} at {self.clicked_at}"
