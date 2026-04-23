# MongoDB migration: SQLAlchemy ORM removed.
# Messages are now embedded as a 'messages' array in the conversations document.


class Conversation:
    """Type-hint stub for MongoDB conversations collection documents."""
    pass


class ConversationMessage:
    """Type-hint stub — messages embedded in conversations document."""
    pass
