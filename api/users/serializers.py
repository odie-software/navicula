from rest_framework import serializers
from .models import UserApplicationSetting
from config.services import ConfigService as AppConfigService # For validating app_id

class UserApplicationSettingSerializer(serializers.ModelSerializer):
    settings = serializers.JSONField() # Explicitly define as JSONField

    class Meta:
        model = UserApplicationSetting
        fields = [
            'id',
            'user_identifier',
            'app_id',
            'settings',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_app_id(self, value):
        """
        Check if the app_id exists in the main application configuration.
        """
        app_config_service = AppConfigService()
        try:
            main_config = app_config_service.load_config()
            if not main_config.apps or value not in main_config.apps:
                raise serializers.ValidationError(f"Application with app_id '{value}' not found in system configuration.")
        except Exception as e: # Catch broader exceptions from config loading
            # Log this error server-side
            # logger.error(f"Could not validate app_id due to config service error: {e}")
            raise serializers.ValidationError(f"Could not validate app_id '{value}' due to a configuration service error.")
        return value

class UserApplicationSettingUpdateSerializer(serializers.ModelSerializer):
    """
    A specific serializer for updating just the 'settings' field.
    The user_identifier and application will be determined from the URL.
    """
    settings = serializers.JSONField() # Explicitly define as JSONField

    class Meta:
        model = UserApplicationSetting
        fields = ['settings']

    def update(self, instance, validated_data):
        instance.settings = validated_data.get('settings', instance.settings)
        instance.save()
        return instance
