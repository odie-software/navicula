import logging
from django.http import JsonResponse, HttpRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services import UserSettingsService, UserSettingsError
from config.services import ConfigService as AppConfigService, ConfigError as AppConfigError
# No specific Pydantic schemas from .schemas are directly used for request/response body here,
# but the service uses them internally.

logger = logging.getLogger(__name__)
DEFAULT_ROLE_FOR_USER_IDENT = 'Guest' # Fallback for user identification if needed, though not strictly for saving.

class UserAppSettingsView(APIView):
    """
    API view to manage user-specific application settings.
    Currently supports POST to update settings for a given app_id for the identified user.
    """
    user_settings_service = UserSettingsService()
    app_config_service = AppConfigService() # To determine how to identify the user

    def _get_user_identifier(self, request: HttpRequest) -> str | None:
        """Helper to identify the user based on app configuration (remote auth or default)."""
        try:
            main_config = self.app_config_service.load_config()
        except AppConfigError:
            logger.error("Could not load main application config to identify user for settings update.")
            # This is an internal error, as main config is needed for user identification logic
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
            # If not using remote auth, Nuxt logic used 'default' user.
            # Check if 'default' user exists in main_config.users
            if main_config.users and 'default' in main_config.users:
                 user_identifier = 'default'
        
        return user_identifier

    def post(self, request: HttpRequest, app_id: str, *args, **kwargs):
        user_identifier = self._get_user_identifier(request)

        if not user_identifier:
            # This implies an issue with either main config loading or user identification logic
            # based on useRemoteAuth settings.
            main_config_loaded = True
            try:
                main_config = self.app_config_service.load_config()
            except AppConfigError:
                main_config_loaded = False
            
            if not main_config_loaded:
                 error_msg = "Forbidden: Cannot identify user due to main configuration error."
                 return JsonResponse({'error': error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif main_config.useRemoteAuth:
                error_msg = "Unauthorized: User identification failed (Remote auth header missing or invalid)."
                return JsonResponse({'error': error_msg}, status=status.HTTP_401_UNAUTHORIZED)
            else: # Not useRemoteAuth, and 'default' user was not found/configured
                error_msg = "Forbidden: Default user not configured for non-remote authentication mode."
                return JsonResponse({'error': error_msg}, status=status.HTTP_403_FORBIDDEN)

        # --- Read Request Body ---
        # The Nuxt version expected body.api_key (string, or empty string to clear)
        # For DRF APIView, request.data will contain the parsed body
        request_data = request.data
        if not isinstance(request_data, dict):
            return JsonResponse({'error': 'Invalid request body: Expected a JSON object.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate expected settings, e.g., api_key.
        # The Nuxt code checked: if typeof body.api_key !== 'string' (allow empty string)
        # This means api_key must be present. If it can be optional, logic changes.
        # For now, let's assume api_key is expected.
        if 'api_key' not in request_data:
            return JsonResponse({'error': "Bad Request: 'api_key' missing in request body."}, status=status.HTTP_400_BAD_REQUEST)
        
        api_key_value = request_data['api_key']
        if not isinstance(api_key_value, str):
             # Allow empty string, but it must be a string
            return JsonResponse({'error': "Bad Request: 'api_key' must be a string."}, status=status.HTTP_400_BAD_REQUEST)

        app_settings_to_save = {'api_key': api_key_value}
        # If other settings were allowed, they would be extracted from request_data here.

        try:
            self.user_settings_service.save_app_settings_for_user(
                user_identifier=user_identifier,
                app_id=app_id,
                new_app_settings_data=app_settings_to_save 
            )
            return Response(
                {'success': True, 'message': f'Settings for {app_id} saved successfully for user {user_identifier}.'},
                status=status.HTTP_200_OK
            )
        except UserSettingsError as e:
            logger.error(f"Error saving user settings for {user_identifier}, app {app_id}: {e}")
            return JsonResponse({'error': str(e)}, status=e.status_code)
        except Exception as e:
            logger.error(f"Unexpected error saving settings for {user_identifier}, app {app_id}: {e}")
            return JsonResponse({'error': 'An unexpected server error occurred while saving settings.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
