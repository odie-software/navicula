from typing import Dict, Optional
from pydantic import BaseModel, Field, RootModel

class AppSpecificSetting(BaseModel):
    """
    Represents settings for a specific application, e.g., an API key.
    This model is flexible to allow various settings per app.
    For now, primarily focusing on api_key.
    """
    api_key: Optional[str] = None

    class Config:
        extra = 'allow' # Allow other app-specific settings

class UserAppSettings(RootModel[Dict[str, AppSpecificSetting]]):
    """
    Represents all app settings for a single user.
    The keys are app IDs.
    Example: {"vikunja_tasks": {"api_key": "secret"}, "another_app": {"url": "..."}}
    """
    root: Dict[str, AppSpecificSetting] = Field(default_factory=dict)

    # Allow direct dictionary-like access if needed
    def __getitem__(self, item):
        return self.root[item]

    def __setitem__(self, key, value):
        self.root[key] = value
    
    def __delitem__(self, key):
        del self.root[key]

    def get(self, key, default=None):
        return self.root.get(key, default)
    
    def keys(self):
        return self.root.keys()

    def items(self):
        return self.root.items()

    def values(self):
        return self.root.values()
    
    def __contains__(self, key):
        return key in self.root
    
    # Pydantic's model_dump() for RootModel handles this correctly by default.
    # If custom logic for dumping the root is needed, it can be overridden.


class AllUserSettings(RootModel[Dict[str, UserAppSettings]]):
    """
    Represents the entire structure of the users.yml file.
    The keys are user identifiers (e.g., email or 'default').
    """
    root: Dict[str, UserAppSettings] = Field(default_factory=dict)

    # Allow direct dictionary-like access
    def __getitem__(self, item):
        return self.root[item]

    def __setitem__(self, key, value):
        self.root[key] = value
        
    def __delitem__(self, key):
        del self.root[key]

    def get(self, key, default=None):
        return self.root.get(key, default)

    # Pydantic's model_dump() for RootModel handles this correctly by default.
