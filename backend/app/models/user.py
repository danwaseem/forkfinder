# MongoDB migration: SQLAlchemy ORM removed.
# Stub classes kept so existing imports throughout routers/services resolve.
# Preferences are now embedded as a subdocument in the users collection.


class User:
    """Type-hint stub for MongoDB users collection documents."""
    pass


class UserPreferences:
    """Type-hint stub — preferences embedded in users document."""
    pass
