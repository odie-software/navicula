import yaml
import logging
from django.conf import settings
from pydantic import ValidationError

from .schemas import Config as PydanticConfig # Alias to avoid confusion

logger = logging.getLogger(__name__)

# Define path to YAML file - should ideally be configurable via Django settings
# For now, assuming it's in the Django project's root directory (api/)
CONFIG_YML_PATH_DEFAULT = settings.BASE_DIR / 'config.yml' # Default if not in settings
CONFIG_YML_PATH = getattr(settings, 'APP_CONFIG_PATH', CONFIG_YML_PATH_DEFAULT)


class ConfigError(Exception):
    """Custom exception for configuration loading errors."""
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.status_code = status_code

class ConfigService:
    def __init__(self, config_path: str = CONFIG_YML_PATH):
        self.config_path = config_path
        self._config_cache: PydanticConfig | None = None

    def _read_and_parse_yaml(self) -> dict:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic check for empty file to prevent YAML load error
            if not content.strip():
                logger.error(f"Config file is empty: {self.config_path}")
                raise ConfigError("Configuration file is empty.", status_code=500)

            raw_config = yaml.safe_load(content)
            if not isinstance(raw_config, dict): # Ensure top level is a dict
                logger.error(f"Config file does not contain a valid YAML dictionary: {self.config_path}")
                raise ConfigError("Invalid configuration format: Root must be a dictionary.", status_code=500)
            return raw_config
        except FileNotFoundError:
            logger.error(f"Config file not found at {self.config_path}")
            raise ConfigError(f"Configuration file not found: {self.config_path}", status_code=500)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML config file at {self.config_path}: {e}")
            raise ConfigError(f"Error parsing configuration file: {e}", status_code=500)
        except Exception as e:
            logger.error(f"Unexpected error reading config file at {self.config_path}: {e}")
            raise ConfigError(f"Unexpected error reading configuration file: {e}", status_code=500)

    def load_config(self, force_reload: bool = False) -> PydanticConfig:
        if self._config_cache is not None and not force_reload:
            return self._config_cache

        raw_config_data = self._read_and_parse_yaml()

        try:
            validated_config = PydanticConfig(**raw_config_data)
            self._config_cache = validated_config
            logger.info(f"Successfully loaded and validated configuration from {self.config_path}")
            return validated_config
        except ValidationError as e:
            logger.error(f"Configuration validation error for {self.config_path}: {e}")
            # Provide a more user-friendly error message if possible
            error_details = e.errors() # Pydantic's detailed errors
            # You might want to format error_details for better logging or response
            raise ConfigError(f"Invalid configuration data: {error_details}", status_code=500)
        except Exception as e: # Catch any other unexpected errors during Pydantic model instantiation
            logger.error(f"Unexpected error instantiating Pydantic Config model from {self.config_path}: {e}")
            raise ConfigError(f"Unexpected error processing configuration data: {e}", status_code=500)

# Global instance (optional, can be instantiated in views)
# config_service_instance = ConfigService()
