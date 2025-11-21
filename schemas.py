"""
Database Schemas for Manga.de

Each Pydantic model below represents a MongoDB collection. The collection
name is the lowercase of the class name (e.g., User -> "user").

These models are used for validation on create/update in the API.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# ------------ Users ------------
class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=24)
    email: EmailStr
    password_hash: str
    bio: Optional[str] = ""
    avatar: Optional[str] = ""  # URL or base64 data URL
    theme: Optional[str] = Field("system", description="light|dark|system")

class PublicUser(BaseModel):
    id: str
    username: str
    avatar: Optional[str] = ""
    bio: Optional[str] = ""

# ------------ Forum ------------
class ForumPost(BaseModel):
    user_id: str
    title: str
    content: str
    tags: List[str] = []
    likes: int = 0

class ForumComment(BaseModel):
    user_id: str
    post_id: str
    content: str

# ------------ Gallery ------------
class GalleryImage(BaseModel):
    user_id: str
    caption: Optional[str] = ""
    image_base64: str  # data URL (e.g., "data:image/png;base64,....")
    likes: int = 0

# ------------ Shop ------------
class Product(BaseModel):
    title: str
    description: Optional[str] = ""
    price: float
    image: Optional[str] = ""  # URL or base64
    stock: int = 0

class Order(BaseModel):
    user_id: str
    items: List[dict]  # [{product_id, quantity}]
    total: float
    status: str = "pending"

# ------------ News ------------
class News(BaseModel):
    title: str
    content: str
    image: Optional[str] = ""
    likes: int = 0

class NewsComment(BaseModel):
    user_id: str
    news_id: str
    content: str

# Utility models for likes/comments
class LikeAction(BaseModel):
    user_id: str

class CommentAction(BaseModel):
    user_id: str
    content: str

# Response helpers
class CreatedResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
