# MongoDB migration: SQLAlchemy ORM removed.
# review_events and restaurant_events are now MongoDB collections written
# by the Kafka worker services.  ObjectId _id (not exposed via API).


class ReviewEvent:
    """Type-hint stub for MongoDB review_events collection documents."""
    pass


class RestaurantEvent:
    """Type-hint stub for MongoDB restaurant_events collection documents."""
    pass
