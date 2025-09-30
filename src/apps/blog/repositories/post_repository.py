"""Post repository."""

from src.core.bases.base_repository import BaseRepository
from src.apps.blog.models.post import Post


class PostRepository(BaseRepository[Post]):
    """Post repository class."""
    
    model = Post
