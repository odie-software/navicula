import logging
from django.http import JsonResponse, HttpRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import NotificationService, NotificationError
from config.services import ConfigService as AppConfigService, ConfigError as AppConfigError
from .schemas import NotificationCountResponse

logger = logging.getLogger(__name__)

class AppNotificationsView(APIView):
    """
    API view to retrieve notification counts for a specific application.
    """
    notification_service = NotificationService()
    app_config_service = AppConfigService() # For user identification

    def _get_user_identifier(self, request: HttpRequest) -> str | None:
        """Helper to identify the user based on app configuration."""
        try:
            main_config = self.app_config_service.load_config()
        except AppConfigError:
            logger.error("Notifications View: Could not load main application config to identify user.")
            return None

        user_identifier = None
        if main_config.useRemoteAuth:
            user_email_header = (
                request.META.get('HTTP_REMOTE_USER') or
                request.META.get('HTTP_X_FORWARDED_USER') or
                ''
            ).lower()
            if user_email_header:
                user_identifier = user_email_header
        else:
            if main_config.users and 'default' in main_config.users:
                user_identifier = 'default'
        
        return user_identifier

    def get(self, request: HttpRequest, app_id: str, *args, **kwargs):
        user_identifier = self._get_user_identifier(request)

        if not user_identifier:
            main_config_loaded = True
            try:
                main_config = self.app_config_service.load_config()
            except AppConfigError:
                main_config_loaded = False

            if not main_config_loaded:
                error_msg = "Forbidden: Cannot identify user due to main configuration error."
                # Return as NotificationCountResponse for consistency if client expects that schema
                return Response(NotificationCountResponse(error=error_msg).model_dump(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif main_config.useRemoteAuth:
                error_msg = "Unauthorized: User identification failed."
                return Response(NotificationCountResponse(error=error_msg).model_dump(), status=status.HTTP_401_UNAUTHORIZED)
            else: # Not useRemoteAuth, and 'default' user was not found/configured
                error_msg = "Forbidden: Default user not configured."
                return Response(NotificationCountResponse(error=error_msg).model_dump(), status=status.HTTP_403_FORBIDDEN)

        try:
            # The service method already returns a NotificationCountResponse Pydantic model
            notification_data: NotificationCountResponse = self.notification_service.get_notification_count(
                user_identifier=user_identifier,
                app_id=app_id
            )
            # .model_dump() converts Pydantic model to dict for DRF Response
            return Response(notification_data.model_dump(), status=status.HTTP_200_OK)
        except NotificationError as e: # Custom errors from the service
            logger.error(f"Notification service error for user {user_identifier}, app {app_id}: {e}")
            return Response(NotificationCountResponse(error=e.error_type or str(e)).model_dump(), status=e.status_code)
        except Exception as e: # Catch-all for unexpected errors
            logger.error(f"Unexpected error fetching notifications for user {user_identifier}, app {app_id}: {e}")
            return Response(
                NotificationCountResponse(error="An unexpected server error occurred.").model_dump(),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
