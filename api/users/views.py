import logging
from django.http import JsonResponse, HttpRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import UserApplicationSetting
from .serializers import UserApplicationSettingSerializer, UserApplicationSettingUpdateSerializer
from config.services import ConfigService as AppConfigService, ConfigError as AppConfigError
from config.schemas import AppLink, NavCategory # Added import

logger = logging.getLogger(__name__)

class UserAppSettingsView(APIView):
    """
    API view to manage user-specific application settings.
    Supports PUT to update/create settings for a given app_id for the identified user.
    Supports GET to retrieve settings for a given app_id for the identified user.
    Supports DELETE to remove settings for a given app_id for the identified user.
    """
    app_config_service = AppConfigService()

    def _get_user_identifier(self, request: HttpRequest) -> str | None:
        """Helper to identify the user based on app configuration (remote auth or default)."""
        try:
            main_config = self.app_config_service.load_config()
        except AppConfigError:
            logger.error("Could not load main application config to identify user for settings update.")
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

    def _validate_app_id(self, app_id: str) -> bool:
        """Helper to validate app_id against main config."""
        try:
            main_config = self.app_config_service.load_config()
            if not main_config or not hasattr(main_config, 'navigationItems'):
                logger.error(f"Main config or navigationItems not found when validating app_id {app_id}.")
                return False

            for item_wrapper in main_config.navigationItems:
                item = item_wrapper.root # Access the actual AppLink or NavCategory from NavigationItem
                if isinstance(item, AppLink):
                    if item.id == app_id:
                        return True
                elif isinstance(item, NavCategory):
                    for app in item.apps:
                        if app.id == app_id:
                            return True
            return False # app_id not found
        except AppConfigError:
            logger.error(f"Could not validate app_id {app_id} due to config service error.")
            return False # Consider this as invalid if config can't be loaded
        except Exception as e:
            logger.error(f"Unexpected error during app_id validation for {app_id}: {e}")
            return False

    def get(self, request: HttpRequest, app_id: str, *args, **kwargs):
        user_identifier = self._get_user_identifier(request)
        if not user_identifier:
            # Error handling similar to PUT/POST for consistency
            return JsonResponse({'error': "User identification failed."}, status=status.HTTP_401_UNAUTHORIZED) # Or 500 if config error

        if not self._validate_app_id(app_id):
            return Response({'error': f"Application with app_id '{app_id}' not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            setting = UserApplicationSetting.objects.get(user_identifier=user_identifier, app_id=app_id)
            serializer = UserApplicationSettingSerializer(setting)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserApplicationSetting.DoesNotExist:
            return Response({'error': 'Settings not found for this user and application.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving settings for user {user_identifier}, app {app_id}: {e}")
            return Response({'error': 'An unexpected server error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request: HttpRequest, app_id: str, *args, **kwargs):
        user_identifier = self._get_user_identifier(request)

        if not user_identifier:
            main_config_loaded = True
            try:
                main_config = self.app_config_service.load_config()
            except AppConfigError:
                main_config_loaded = False
            
            if not main_config_loaded:
                 error_msg = "Forbidden: Cannot identify user due to main configuration error."
                 return JsonResponse({'error': error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif hasattr(main_config, 'useRemoteAuth') and main_config.useRemoteAuth: # Check if main_config was loaded
                error_msg = "Unauthorized: User identification failed (Remote auth header missing or invalid)."
                return JsonResponse({'error': error_msg}, status=status.HTTP_401_UNAUTHORIZED)
            else: 
                error_msg = "Forbidden: Default user not configured or user identification failed for non-remote authentication mode."
                return JsonResponse({'error': error_msg}, status=status.HTTP_403_FORBIDDEN)

        if not self._validate_app_id(app_id):
            return Response({'error': f"Application with app_id '{app_id}' not found in system configuration."}, status=status.HTTP_400_BAD_REQUEST)

        request_data_settings = request.data 
        # The UserApplicationSettingUpdateSerializer expects a dict with a 'settings' key
        # The old code expected request.data = {'api_key': 'value'}
        # We need to ensure the data passed to the serializer is {'settings': {'api_key': 'value', ...}}
        
        # For now, let's assume the request body IS the content of the 'settings' field.
        # e.g. PUT body: {"api_key": "new_key", "another_setting": "value"}
        # This matches the spirit of the old UserSettingsService.save_app_settings_for_user's new_app_settings_data
        
        data_for_serializer = {'settings': request_data_settings}

        try:
            setting, created = UserApplicationSetting.objects.get_or_create(
                user_identifier=user_identifier,
                app_id=app_id,
                defaults={'settings': {}} # Default settings if creating
            )
            
            # Use UserApplicationSettingUpdateSerializer for partial updates to the 'settings' field
            serializer = UserApplicationSettingUpdateSerializer(setting, data=data_for_serializer, partial=True)
            if serializer.is_valid():
                serializer.save()
                # For the response, serialize the full object to show current state
                full_serializer = UserApplicationSettingSerializer(setting)
                return Response(full_serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error saving settings for user {user_identifier}, app {app_id}: {e}")
            return Response({'error': 'An unexpected server error occurred while saving settings.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request: HttpRequest, app_id: str, *args, **kwargs):
        user_identifier = self._get_user_identifier(request)
        if not user_identifier:
            return JsonResponse({'error': "User identification failed."}, status=status.HTTP_401_UNAUTHORIZED)

        if not self._validate_app_id(app_id):
            return Response({'error': f"Application with app_id '{app_id}' not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            setting = UserApplicationSetting.objects.get(user_identifier=user_identifier, app_id=app_id)
            setting.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserApplicationSetting.DoesNotExist:
            return Response({'error': 'Settings not found for this user and application.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting settings for user {user_identifier}, app {app_id}: {e}")
            return Response({'error': 'An unexpected server error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
