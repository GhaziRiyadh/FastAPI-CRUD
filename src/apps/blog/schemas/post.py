"""Post schemas."""

from typing import Optional
from pydantic import BaseModel


class PostCreate(BaseModel):
    """Schema for creating a post."""
    title: str
    content: str
    author: str


class PostUpdate(BaseModel):
    """Schema for updating a post."""
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None

