from django.db import models
from django.conf import settings

class UserApplicationSetting(models.Model):
    """
    Stores specific settings for a user related to a particular application.
    """
    # If using Django's built-in User model and you want to link directly:
    # user = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.CASCADE,
    #     related_name="app_settings"
    # )
    # For now, sticking to user_identifier as per existing logic:
    user_identifier = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Identifier for the user (e.g., email or 'default')."
    )
    app_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Identifier for the application (e.g., 'app-vikunja'). Must match an app_id in the main config."
    )
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Application-specific settings for the user (e.g., {'api_key': '...'})."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.user_identifier} in {self.app_id}"

    class Meta:
        verbose_name = "User Application Setting"
        verbose_name_plural = "User Application Settings"
        unique_together = ('user_identifier', 'app_id') # Ensures one settings entry per user per app
        ordering = ['user_identifier', 'app_id']
