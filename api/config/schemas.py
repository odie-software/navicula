from typing import List, Dict, Union, Optional, Literal
from pydantic import BaseModel, Field, validator, RootModel

# Forward references for Pydantic models
# Not strictly necessary here as definitions are ordered, but good practice for complex schemas
class AppLink(BaseModel):
    id: str
    title: str # Changed from name
    icon: str
    url: str
    type: Optional[str] = None
    # Allow any other fields (e.g. target, description)
    class Config:
        extra = 'allow'

class NavCategory(BaseModel):
    id: str
    title: str # Changed from name
    icon: str
    apps: List[AppLink]
    # Allow any other fields
    class Config:
        extra = 'allow'

# Using a discriminated union for NavigationItem
# Pydantic v2 recommends using Union with discriminated types
# We can infer the type by checking for 'url' or 'apps'
# However, for parsing from YAML, it's often easier to define a custom RootModel or validator
# if the structure isn't perfectly clean for discriminated unions.
# For now, let's define them separately and handle the union in the main Config model.

class NavigationItem(RootModel[Union[AppLink, NavCategory]]):
    root: Union[AppLink, NavCategory]

    @validator('root', pre=True, allow_reuse=True)
    def _validate_root_type(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Navigation item must be a dictionary")
        if 'url' in v and 'apps' not in v:
            return AppLink(**v)
        if 'apps' in v and 'url' not in v:
            return NavCategory(**v)
        raise ValueError("Navigation item must be either an AppLink (with 'url') or a NavCategory (with 'apps')")


class Role(BaseModel):
    permissions: List[str]
    # Allow any other fields
    class Config:
        extra = 'allow'

class UserConfig(BaseModel):
    role: str
    # Allow any other fields
    class Config:
        extra = 'allow'

class Config(BaseModel):
    navigationItems: List[NavigationItem] = Field(default_factory=list)
    roles: Dict[str, Role] = Field(default_factory=dict)
    users: Dict[str, UserConfig] = Field(default_factory=dict)
    defaultToolbarColor: str = 'primary'
    keybindings: Dict[str, str] = Field(default_factory=dict)
    useRemoteAuth: bool = False
    # Allow any other fields at the root of the config
    class Config:
        extra = 'allow'
