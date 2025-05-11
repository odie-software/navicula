import logging
from django.http import JsonResponse, HttpRequest
from rest_framework.views import APIView
from rest_framework.response import Response # DRF's Response handles serialization better
from rest_framework import status

from .services import ConfigService, ConfigError
from .schemas import AppLink, NavCategory, Role as PydanticRole, UserConfig as PydanticUserConfig, Config as PydanticConfig

logger = logging.getLogger(__name__)

DEFAULT_ROLE = 'Guest' # As defined in original logic

class ConfigurationDetailView(APIView):
    """
    API view to retrieve the application configuration.
    It processes a YAML configuration file, determines user context,
    and filters navigation items based on user roles and permissions.
    """
    config_service = ConfigService() # Can be instantiated per request or globally

    def get(self, request: HttpRequest, *args, **kwargs):
        try:
            config: PydanticConfig = self.config_service.load_config()
        except ConfigError as e:
            logger.error(f"Configuration loading failed: {e}")
            return JsonResponse({'error': str(e)}, status=e.status_code)
        except Exception as e: # Catch any other unexpected error
            logger.error(f"Unexpected error during configuration loading: {e}")
            return JsonResponse({'error': 'An unexpected server error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- User Identification & Role Calculation ---
        user_email: str | None = None
        user_identifier: str | None = None
        # user_pydantic_config: PydanticUserConfig | None = None # From Pydantic model
        user_role_name: str

        if config.useRemoteAuth:
            user_email_header = (
                request.META.get('HTTP_REMOTE_USER') or
                request.META.get('HTTP_X_FORWARDED_USER') or
                ''
            ).lower()
            user_email = user_email_header or None
            user_identifier = user_email
            user_pydantic_config = config.users.get(user_identifier) if user_identifier and config.users else None
            user_role_name = user_pydantic_config.role if user_pydantic_config else DEFAULT_ROLE
        else:
            user_identifier = 'default'
            user_pydantic_config = config.users.get(user_identifier) if config.users else None
            user_role_name = user_pydantic_config.role if user_pydantic_config else DEFAULT_ROLE
            user_email = f"{user_identifier}@navicula.local" if user_pydantic_config else None
        
        user_pydantic_role: PydanticRole | None = config.roles.get(user_role_name) if config.roles else None

        if not user_pydantic_role:
            logger.warning(
                f'Assigned role "{user_role_name}" for user "{user_identifier}" not found in roles definition. '
                f'Falling back to "{DEFAULT_ROLE}".'
            )
            user_role_name = DEFAULT_ROLE
            user_pydantic_role = config.roles.get(DEFAULT_ROLE) if config.roles else None

        if not user_pydantic_role:
            logger.error(f'Default role "{DEFAULT_ROLE}" or assigned role "{user_role_name}" not found in config')
            return JsonResponse({
                'error': 'Server configuration error: Role definition missing',
                'userEmail': user_email,
                'role': DEFAULT_ROLE,
                'navigationItems': [],
                'defaultToolbarColor': config.defaultToolbarColor,
                'keybindings': config.keybindings,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user_permissions = set(user_pydantic_role.permissions)
        has_wildcard = '*' in user_permissions

        # --- Filtering Navigation Items ---
        accessible_navigation_items_data = []
        for nav_item_wrapper in config.navigationItems:
            item = nav_item_wrapper.root # Access the actual AppLink or NavCategory
            
            # Common properties
            item_id = item.id
            
            if isinstance(item, AppLink):
                if has_wildcard or user_permissions.has(item_id):
                    accessible_navigation_items_data.append(item.model_dump())
            elif isinstance(item, NavCategory):
                can_access_category = has_wildcard or user_permissions.has(item_id)
                accessible_apps_data = []
                for app in item.apps:
                    if has_wildcard or user_permissions.has(app.id) or can_access_category:
                        accessible_apps_data.append(app.model_dump())
                
                if accessible_apps_data:
                    # Create a new dict for the category to avoid modifying original Pydantic model
                    category_data = item.model_dump()
                    category_data['apps'] = accessible_apps_data
                    accessible_navigation_items_data.append(category_data)
        
        response_data = {
            'userEmail': user_email,
            'role': user_role_name,
            'navigationItems': accessible_navigation_items_data,
            'defaultToolbarColor': config.defaultToolbarColor,
            'keybindings': config.keybindings,
        }
        return Response(response_data, status=status.HTTP_200_OK)
