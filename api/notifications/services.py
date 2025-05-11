import logging
import httpx
from typing import List, Optional, Dict

from config.services import ConfigService as AppConfigService, ConfigError as AppConfigError
from config.schemas import AppLink # To get app_url and app_type
from users.services import UserSettingsService, UserSettingsError
from users.schemas import AppSpecificSetting # To get api_key
from .schemas import NotificationCountResponse, ExternalNotificationItem # For response and parsing external data

logger = logging.getLogger(__name__)

class NotificationError(Exception):
    """Custom exception for notification fetching errors."""
    def __init__(self, message, error_type: Optional[str] = "fetch_failed", status_code=500):
        super().__init__(message)
        self.error_type = error_type # e.g., 'unauthorized', 'timeout', 'config_missing'
        self.status_code = status_code


class NotificationService:
    def __init__(self):
        self.app_config_service = AppConfigService()
        self.user_settings_service = UserSettingsService()

    def _find_app_link(self, app_id: str) -> Optional[AppLink]:
        """Finds an AppLink by its ID from the main configuration."""
        try:
            config = self.app_config_service.load_config()
            for nav_item_wrapper in config.navigationItems:
                item = nav_item_wrapper.root
                if isinstance(item, AppLink) and item.id == app_id:
                    return item
                elif hasattr(item, 'apps'): # NavCategory
                    for app in item.apps:
                        if app.id == app_id:
                            return app
            return None
        except AppConfigError:
            logger.error(f"Notifications: Could not load main config to find app {app_id}.")
            return None

    def _get_user_app_api_key(self, user_identifier: str, app_id: str) -> Optional[str]:
        """Gets the API key for a specific app for a user."""
        try:
            user_app_settings = self.user_settings_service.get_settings_for_user(user_identifier)
            if app_id in user_app_settings:
                specific_app_settings: AppSpecificSetting = user_app_settings[app_id]
                return specific_app_settings.api_key
            return None
        except UserSettingsError:
            logger.error(f"Notifications: Could not load user settings for user {user_identifier}, app {app_id}.")
            return None

    def _fetch_vikunja_notifications(self, app_url: str, api_key: str, user_identifier: str, app_id: str) -> NotificationCountResponse:
        base_url = app_url.rstrip('/')
        api_url = f"{base_url}/api/v1/notifications"
        
        logger.info(f"Fetching Vikunja notifications from {api_url} for user {user_identifier}, app {app_id}")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(api_url, headers=headers)
            
            if response.status_code == 401:
                logger.warning(f"Notifications: Unauthorized access to Vikunja API ({app_id}) for user {user_identifier}. Check API key.")
                return NotificationCountResponse(count=None, error="unauthorized")
            
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            
            notifications_data = response.json()
            if not isinstance(notifications_data, list):
                logger.warning(f"Notifications: Unexpected response format from Vikunja ({app_id}) for user {user_identifier}. Expected list.")
                return NotificationCountResponse(count=None, error="fetch_failed")

            # Parse with Pydantic model for safety, though only 'read_at' is used
            unread_count = 0
            for raw_item in notifications_data:
                try:
                    item = ExternalNotificationItem.model_validate(raw_item)
                    if item.read_at is None:
                        unread_count += 1
                except Exception: # Pydantic ValidationError or other
                    logger.warning(f"Skipping invalid notification item from Vikunja: {raw_item}")
            
            logger.info(f"Vikunja notifications count for {app_id} / {user_identifier}: {unread_count}")
            return NotificationCountResponse(count=unread_count)

        except httpx.TimeoutException:
            logger.warning(f"Notifications: Timeout fetching data from Vikunja ({app_id}) for user {user_identifier}.")
            return NotificationCountResponse(count=None, error="timeout")
        except httpx.HTTPStatusError as e:
            logger.error(f"Notifications: HTTP error from Vikunja ({app_id}) for user {user_identifier}: {e.response.status_code} - {e.response.text}")
            return NotificationCountResponse(count=None, error="fetch_failed")
        except httpx.RequestError as e:
            logger.error(f"Notifications: Request error for Vikunja ({app_id}) for user {user_identifier}: {e}")
            return NotificationCountResponse(count=None, error="fetch_failed")
        except Exception as e: # Catch-all for other issues like JSON parsing
            logger.error(f"Notifications: Unexpected error processing Vikunja response ({app_id}) for user {user_identifier}: {e}")
            return NotificationCountResponse(count=None, error="fetch_failed")


    def get_notification_count(self, user_identifier: str, app_id: str) -> NotificationCountResponse:
        app_link = self._find_app_link(app_id)
        if not app_link:
            logger.warning(f"Notifications: AppLink with ID '{app_id}' not found in configuration.")
            # Nuxt returned { count: null } for unknown apps, which is fine.
            return NotificationCountResponse(count=None, error="app_not_found") 
        
        if not app_link.type:
            logger.info(f"Notifications: App '{app_id}' (type: {app_link.name}) does not support notifications (no type defined).")
            return NotificationCountResponse(count=None) # No error, just no count

        api_key = self._get_user_app_api_key(user_identifier, app_id)
        if not api_key:
            logger.warning(f"Notifications: Missing api_key for {app_link.type} ({app_id}) for user {user_identifier}. Cannot fetch.")
            # Nuxt returned { count: null } if API key missing, not an error to the client.
            return NotificationCountResponse(count=None, error="config_missing_apikey")

        if app_link.type == 'vikunja':
            return self._fetch_vikunja_notifications(app_link.url, api_key, user_identifier, app_id)
        # Add other app types here
        # elif app_link.type == 'another-service':
        #     pass
        else:
            logger.info(f"Notifications: Unsupported type \"{app_link.type}\" for app {app_id}")
            return NotificationCountResponse(count=None) # Type defined but not handled
