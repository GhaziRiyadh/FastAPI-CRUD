"""Post service."""

from typing import Any, Dict
from src.core.bases.base_service import BaseService
from src.apps.blog.repositories.post_repository import PostRepository
from src.apps.blog.models.post import Post


class PostService(BaseService[Post]):
    """Post service class."""
    
    def __init__(self, repository: PostRepository):
        super().__init__(repository)

    async def _validate_create(self, create_data: Dict[str, Any]) -> None:
        """Validate data before creation."""
        # Add your business logic validation here
        pass

    async def _validate_update(
        self, 
        item_id: Any, 
        update_data: Dict[str, Any], 
        existing_item: Post
    ) -> None:
        """Validate data before update."""
        # Add your business logic validation here
        pass

    async def _validate_delete(self, item_id: Any, existing_item: Post) -> None:
        """Validate before soft delete."""
        # Add your business logic validation here
        pass

    async def _validate_force_delete(self, item_id: Any, existing_item: Post) -> None:
        """Validate before force delete."""
        # Add your business logic validation here
        pass
