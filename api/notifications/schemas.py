from typing import Optional
from pydantic import BaseModel

class NotificationCountResponse(BaseModel):
    """
    Response schema for the notification count endpoint.
    """
    count: Optional[int] = None
    error: Optional[str] = None # To indicate issues like 'unauthorized', 'timeout', 'fetch_failed'

# Example schema for an external notification item, if needed for more complex parsing.
# For Vikunja, it was checking for a 'read_at' property.
class ExternalNotificationItem(BaseModel):
    read_at: Optional[str] = None

    class Config:
        extra = 'allow' # Allow other fields from the external API
