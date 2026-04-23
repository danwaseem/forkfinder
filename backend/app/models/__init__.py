# MongoDB migration: model classes are now lightweight stubs used only as type hints.
# All data access goes through pymongo in the service and router layers.
from .user import User, UserPreferences
from .restaurant import Restaurant, RestaurantClaim
from .review import Review
from .favorite import Favorite
from .conversation import Conversation, ConversationMessage
from .events import ReviewEvent, RestaurantEvent

__all__ = [
    "User",
    "UserPreferences",
    "Restaurant",
    "RestaurantClaim",
    "Review",
    "Favorite",
    "Conversation",
    "ConversationMessage",
    "ReviewEvent",
    "RestaurantEvent",
]
