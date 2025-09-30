"""Post router."""

from src.core.database import get_session
from src.core.bases.base_router import BaseRouter
from src.apps.blog.services.post_service import PostService
from src.apps.blog.repositories.post_repository import PostRepository
from src.apps.blog.schemas.post import PostCreate, PostUpdate


def get_post_repository():
    """Get post repository instance."""
    return PostRepository(get_session) #type:ignore


def get_post_service():
    """Get post service instance."""
    repository = get_post_repository()
    return PostService(repository)


class PostRouter(BaseRouter):
    """Post router class."""
    
    def __init__(self):
        super().__init__(
            service=get_post_service(),
            create_schema=PostCreate,
            update_schema=PostUpdate,
            prefix="/posts",
            tags=["Posts"]
        )


# Router instance
router = PostRouter().get_router()
