from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, DateTime, Enum, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import relationship

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("user", "owner"), default="user", nullable=False)

    # Profile fields
    phone = Column(String(50))
    about_me = Column(Text)
    city = Column(String(100))
    state = Column(String(10))
    country = Column(String(100))
    languages = Column(String(500))  # comma-separated
    gender = Column(String(50))
    profile_photo_url = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    preferences = relationship(
        "UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    restaurants_created = relationship(
        "Restaurant", foreign_keys="Restaurant.created_by", back_populates="creator"
    )
    restaurants_claimed = relationship(
        "Restaurant", foreign_keys="Restaurant.claimed_by", back_populates="owner"
    )
    claims = relationship("RestaurantClaim", back_populates="owner_user")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    cuisine_preferences = Column(Text)            # JSON array: ["Italian", "Sushi"]
    price_range = Column(String(20))              # "$" | "$$" | "$$$" | "$$$$"
    search_radius = Column(Integer, default=10)   # miles (1–500)
    preferred_locations = Column(Text)            # JSON array: ["San Francisco", "Oakland"]
    dietary_restrictions = Column(Text)           # JSON array: ["Gluten-Free", "Vegan"]
    ambiance_preferences = Column(Text)           # JSON array: ["Casual", "Outdoor Seating"]
    sort_preference = Column(String(50), default="rating")  # rating|newest|most_reviewed|price_asc|price_desc

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preferences")
