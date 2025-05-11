import yaml
import logging
import os
from django.conf import settings
from pydantic import ValidationError

from .schemas import AllUserSettings, UserAppSettings, AppSpecificSetting
from config.services import ConfigService as AppConfigService # To get useRemoteAuth flag

logger = logging.getLogger(__name__)

# Path to users.yml
USERS_YML_PATH_DEFAULT = settings.BASE_DIR / 'users.yml'
USERS_YML_PATH = getattr(settings, 'APP_USER_SETTINGS_PATH', USERS_YML_PATH_DEFAULT)

class UserSettingsError(Exception):
    """Custom exception for user settings errors."""
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.status_code = status_code

class UserSettingsService:
    def __init__(self, users_file_path: str = USERS_YML_PATH):
        self.users_file_path = users_file_path
        # self.app_config_service = AppConfigService() # If needed to check useRemoteAuth for user identification

    def _read_users_yaml(self) -> dict:
        try:
            # Ensure directory exists, though for BASE_DIR it should.
            # os.makedirs(os.path.dirname(self.users_file_path), exist_ok=True)
            with open(self.users_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip(): # Handle empty file
                return {}
                
            raw_data = yaml.safe_load(content)
            if raw_data is None: # If file is empty or just comments
                return {}
            if not isinstance(raw_data, dict):
                logger.error(f"User settings file does not contain a valid YAML dictionary: {self.users_file_path}")
                raise UserSettingsError("Invalid user settings format: Root must be a dictionary.", status_code=500)
            return raw_data
        except FileNotFoundError:
            # If the file doesn't exist, it's not an error for loading, just means no settings yet.
            logger.info(f"User settings file not found at {self.users_file_path}. Returning empty settings.")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML user settings file at {self.users_file_path}: {e}")
            raise UserSettingsError(f"Error parsing user settings file: {e}", status_code=500)
        except Exception as e:
            logger.error(f"Unexpected error reading user settings file at {self.users_file_path}: {e}")
            raise UserSettingsError(f"Unexpected error reading user settings file: {e}", status_code=500)

    def _write_users_yaml(self, data: AllUserSettings) -> None:
        try:
            # Ensure directory exists before writing
            os.makedirs(os.path.dirname(self.users_file_path), exist_ok=True)
            with open(self.users_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data.model_dump(), f, sort_keys=True, allow_unicode=True) # Use model_dump for Pydantic
            logger.info(f"Successfully wrote user settings to {self.users_file_path}")
        except Exception as e:
            logger.error(f"Error writing user settings file to {self.users_file_path}: {e}")
            raise UserSettingsError(f"Could not save user settings: {e}", status_code=500)

    def load_all_user_settings(self) -> AllUserSettings:
        raw_data = self._read_users_yaml()
        try:
            # Pydantic will create default UserAppSettings if a user exists but has no settings.
            return AllUserSettings.model_validate(raw_data)
        except ValidationError as e:
            logger.error(f"User settings validation error for {self.users_file_path}: {e}")
            raise UserSettingsError(f"Invalid user settings data: {e.errors()}", status_code=500)

    def get_settings_for_user(self, user_identifier: str) -> UserAppSettings:
        all_settings = self.load_all_user_settings()
        # Pydantic model will return a default UserAppSettings (empty dict) if key not found due to __root__ default_factory
        user_specific_settings_dict = all_settings.get(user_identifier, {}) # Get the raw dict for this user
        return UserAppSettings.model_validate(user_specific_settings_dict)


    def save_app_settings_for_user(
        self, 
        user_identifier: str, 
        app_id: str, 
        new_app_settings_data: dict # e.g. {"api_key": "new_key"}
    ) -> None:
        if not user_identifier:
            raise UserSettingsError("User identifier cannot be empty.", status_code=400)
        if not app_id:
            raise UserSettingsError("App ID cannot be empty.", status_code=400)

        all_settings = self.load_all_user_settings()

        # Get current settings for the user, or initialize if user is new
        current_user_app_settings_dict = all_settings.get(user_identifier, {})
        current_user_app_settings = UserAppSettings.model_validate(current_user_app_settings_dict)


        # Get current settings for the specific app, or initialize if app is new for this user
        app_settings_dict = current_user_app_settings.get(app_id, {})
        app_settings = AppSpecificSetting.model_validate(app_settings_dict)

        # Update the app_settings based on new_app_settings_data
        # For now, assuming new_app_settings_data is like {"api_key": "..."}
        if 'api_key' in new_app_settings_data:
            api_key_value = new_app_settings_data['api_key']
            if api_key_value == '' or api_key_value is None: # Clearing the key
                app_settings.api_key = None
            else:
                app_settings.api_key = str(api_key_value)
        
        # Update other potential fields if they exist in new_app_settings_data and AppSpecificSetting
        for key, value in new_app_settings_data.items():
            if key != 'api_key' and hasattr(app_settings, key):
                setattr(app_settings, key, value)


        # Put the updated/new app settings back into the user's settings
        # Only update if there are actual settings for the app
        if app_settings.model_dump(exclude_none=True): # if app_settings is not empty
             current_user_app_settings[app_id] = app_settings
        elif app_id in current_user_app_settings: # if app_settings became empty, remove it
            del current_user_app_settings[app_id]


        # Put the user's updated settings back into all_settings
        # Only update if the user has any app settings left
        if current_user_app_settings.model_dump(): # if user_settings is not empty
            all_settings[user_identifier] = current_user_app_settings
        elif user_identifier in all_settings: # if user_settings became empty, remove the user
            del all_settings[user_identifier]
            
        self._write_users_yaml(all_settings)
