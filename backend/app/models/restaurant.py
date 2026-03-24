from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship

from ..database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    cuisine_type = Column(String(100), index=True)
    price_range = Column(String(20))  # "$", "$$", "$$$", "$$$$"

    # Location
    address = Column(String(500))
    city = Column(String(100), index=True)
    state = Column(String(10))
    country = Column(String(100))
    zip_code = Column(String(20))
    latitude = Column(Float)
    longitude = Column(Float)

    # Contact
    phone = Column(String(50))
    website = Column(String(500))

    # JSON fields stored as text
    hours = Column(Text)   # JSON: {"monday": "9am-9pm", ...}
    photos = Column(Text)  # JSON: ["url1", "url2"]

    # Stats (denormalized for performance)
    avg_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)

    # Ownership
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    claimed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_claimed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship(
        "User", foreign_keys=[created_by], back_populates="restaurants_created"
    )
    owner = relationship(
        "User", foreign_keys=[claimed_by], back_populates="restaurants_claimed"
    )
    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="restaurant", cascade="all, delete-orphan")
    claims = relationship("RestaurantClaim", back_populates="restaurant")


class RestaurantClaim(Base):
    __tablename__ = "restaurant_claims"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum("pending", "approved", "rejected"), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="claims")
    owner_user = relationship("User", back_populates="claims")
