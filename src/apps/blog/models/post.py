"""Post model."""

from sqlmodel import Field
from src.core.database import BaseModel


class Post(BaseModel, table=True):
    """Post model class."""
    
    __tablename__ = "blog_posts"  # type: ignore
    title: str = Field()
    content: str = Field()
    author: str = Field()

