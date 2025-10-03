from typing import Any, Dict, Generic, List, TypeVar, Union
from unittest import result
from pydantic import BaseModel

from src.core.bases.base_repository import BaseRepository
from src.core import exceptions
from src.core.response.schemas import PaginatedResponse

T = TypeVar("T")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[T]):
    """Base service class with common CRUD operations and standardized responses."""

    def __init__(self, repository: BaseRepository) -> None:
        self.repository = repository

    async def _return_one_data(self, data: T):
        return data

    async def _return_multi_data(self, data: List[T]):
        return data

    async def get_by_id(
        self, item_id: Any, include_deleted: bool = False, **filters
    ) -> Dict[str, Any]:
        """Get a single item by ID."""
        try:
            item = await self.repository.get(
                item_id=item_id, include_deleted=include_deleted, **filters
            )

            if not item:
                raise exceptions.NotFoundException(
                    detail=f"Item with id {item_id} not found"
                )

            return {
                "data": await self._return_one_data(item),
                "message": "Item retrieved successfully",
            }
        except exceptions.NotFoundException:
            raise
        except Exception as e:
            raise exceptions.ServiceException(
                detail=f"Error retrieving item: {str(e)}"
            ) from e

    async def get_list(
        self,
        page: int = 1,
        per_page: int = 10,
        include_deleted: bool = False,
        **filters,
    ) -> Dict[str, Any]:
        """Get paginated list of items."""
        try:
            # Validate pagination parameters
            if page < 1:
                page = 1
            if per_page < 1 or per_page > 100:
                per_page = 10

            result = await self.repository.list(
                page=page, per_page=per_page, include_deleted=include_deleted, **filters
            )

            return await self._result_to_pagenation_response(result)
        except Exception as e:
            raise exceptions.ServiceException(
                detail=f"Error retrieving items list: {str(e)}"
            ) from e

    async def get_many(
        self, skip: int = 0, limit: int = 100, include_deleted: bool = False, **filters
    ) -> Dict[str, Any]:
        """Get multiple items without pagination metadata."""
        try:
            items = await self.repository.get_many(
                skip=skip, limit=limit, include_deleted=include_deleted, **filters
            )

            return {
                "data": await self._return_multi_data(items),
                "message": f"Retrieved {len(items)} items successfully",
            }
        except Exception as e:
            raise exceptions.ServiceException(
                detail=f"Error retrieving items: {str(e)}"
            ) from e

    async def create(
        self, obj_in: Union[Dict[str, Any], BaseModel], **additional_data
    ) -> Dict[str, Any]:
        """Create a new item."""
        try:
            # Convert Pydantic model to dict if needed
            if isinstance(obj_in, BaseModel):
                create_data = obj_in.model_dump(exclude_unset=True)
            else:
                create_data = obj_in.copy()

            # Merge with additional data
            create_data.update(additional_data)

            # Validate business rules before creation
            await self._validate_create(create_data)

            item = await self.repository.create(create_data)

            return {
                "data": await self._return_one_data(item),
                "message": "Item created successfully",
            }
        except exceptions.ValidationException:
            raise
        except Exception as e:
            raise exceptions.ServiceException(
                detail=f"Error creating item: {str(e)}"
            ) from e

    async def update(
        self,
        item_id: Any,
        obj_in: Union[Dict[str, Any], BaseModel],
        exclude_unset: bool = True,
        **additional_data,
    ) -> Dict[str, Any]:
        """Update an existing item."""
        try:
            # Check if item exists
            existing_item = await self.repository.get(item_id)
            if not existing_item:
                raise exceptions.NotFoundException(
                    detail=f"Item with id {item_id} not found"
                )

            # Convert Pydantic model to dict if needed
            if isinstance(obj_in, BaseModel):
                update_data = obj_in.model_dump(exclude_unset=exclude_unset)
            else:
                update_data = obj_in.copy()

            # Merge with additional data
            update_data.update(additional_data)

            # Validate business rules before update
            await self._validate_update(item_id, update_data, existing_item)

            updated_item = await self.repository.update(
                item_id=item_id, obj_in=update_data
            )

            if not updated_item:
                raise exceptions.NotFoundException(
                    detail=f"Item with id {item_id} not found during update"
                )

            return {
                "data": await self._return_one_data(updated_item),
                "message": "Item updated successfully",
            }
        except (exceptions.NotFoundException, exceptions.ValidationException):
            raise
        except Exception as e:
            raise exceptions.ServiceException(
                detail=f"Error updating item: {str(e)}"
            ) from e

    async def soft_delete(self, item_id: Any) -> Dict[str, Any]:
        """Soft delete an item."""
        try:
            # Check if item exists
            existing_item = await self.repository.get(item_id)
            if not existing_item:
                raise exceptions.NotFoundException(
                    detail=f"Item with id {item_id} not found"
                )

            # Validate if soft delete is allowed
            await self._validate_delete(item_id, existing_item)

            success = await self.repository.soft_delete(item_id)

            if not success:
                raise exceptions.OperationException(
                    detail=f"Failed to soft delete item with id {item_id}"
                )

            return {"data": None, "message": "Item soft deleted successfully"}
        except (exceptions.NotFoundException, exceptions.ValidationException):
            raise
        except Exception as e:
            raise exceptions.ServiceException(
                detail=f"Error soft deleting item: {str(e)}"
            ) from e

    async def restore(self, item_id: Any) -> Dict[str, Any]:
        """Restore a soft deleted item."""
        try:
            success = await self.repository.restore(item_id)

            if not success:
                raise exceptions.NotFoundException(
                    detail=f"Item with id {item_id} not found or not deleted"
                )

            return {"data": None, "message": "Item restored successfully"}
        except exceptions.NotFoundException:
            raise
        except Exception as e:
            raise exceptions.ServiceException(
                detail=f"Error restoring item: {str(e)}"
            ) from e

    async def force_delete(self, item_id: Any) -> Dict[str, Any]:
        """Permanently delete an item."""
        try:
            # Check if item exists
            existing_item = await self.repository.get(item_id, include_deleted=True)
            if not existing_item:
                raise exceptions.NotFoundException(
                    detail=f"Item with id {item_id} not found"
                )

            # Validate if force delete is allowed
            await self._validate_force_delete(item_id, existing_item)

            success = await self.repository.force_delete(item_id)

            if not success:
                raise exceptions.OperationException(
                    detail=f"Failed to delete item with id {item_id}"
                )

            return {"data": None, "message": "Item permanently deleted successfully"}
        except (exceptions.NotFoundException, exceptions.ValidationException):
            raise
        except Exception as e:
            raise exceptions.ServiceException(
                detail=f"Error deleting item: {str(e)}"
            ) from e

    async def exists(
        self, item_id: Any, include_deleted: bool = False
    ) -> Dict[str, Any]:
        """Check if an item exists."""
        try:
            exists = await self.repository.exists(
                item_id, include_deleted=include_deleted
            )

            return {
                "data": {"exists": exists},
                "message": f"Item {'exists' if exists else 'does not exist'}",
            }
        except Exception as e:
            raise exceptions.ServiceException(
                detail=f"Error checking item existence: {str(e)}"
            ) from e

    async def count(self, include_deleted: bool = False, **filters) -> Dict[str, Any]:
        """Count items matching filters."""
        try:
            count = await self.repository.count(
                include_deleted=include_deleted, **filters
            )

            return {"data": {"count": count}, "message": f"Found {count} items"}
        except Exception as e:
            raise exceptions.ServiceException(
                detail=f"Error counting items: {str(e)}"
            ) from e

    async def bulk_create(
        self, objs_in: List[Union[Dict[str, Any], BaseModel]], **additional_data
    ) -> Dict[str, Any]:
        """Create multiple items in bulk."""
        try:
            create_data_list = []
            for obj_in in objs_in:
                if isinstance(obj_in, BaseModel):
                    create_data = obj_in.model_dump(exclude_unset=True)
                else:
                    create_data = obj_in.copy()

                await self._validate_create(create_data)

                create_data.update(additional_data)
                create_data_list.append(create_data)

            items = await self.repository.bulk_create(create_data_list)

            return {
                "data": await self._return_multi_data(items),
                "message": f"Successfully created {len(items)} items",
            }
        except exceptions.ValidationException:
            raise
        except Exception as e:
            raise exceptions.ServiceException(
                detail=f"Error in bulk creating items: {str(e)}"
            ) from e

    async def bulk_update(
        self, objs_in: List[Union[Dict[str, Any], BaseModel]], **additional_data
    ) -> Dict[str, Any]:
        """Create multiple items in bulk."""
        try:
            update_data_list = []
            for obj_in in objs_in:
                id = (
                    obj_in.get("id")
                    if isinstance(obj_in, dict)
                    else obj_in.id  # type:ignore
                )
                if not id:
                    raise exceptions.ValidationException(
                        detail="ID is required for bulk update"
                    )
                obj = (
                    obj_in.get("data")
                    if isinstance(obj_in, dict)
                    else obj_in.data  # type:ignore
                )
                if isinstance(obj, BaseModel):
                    update_data = obj.model_dump(exclude_unset=True)
                else:
                    update_data = obj.copy()  # type:ignore

                await self._validate_update(update_data.get("id"), update_data, await self.repository.get(id))  # type: ignore

                update_data.update(additional_data)
                update_data_list.append(update_data)

            items = await self.repository.bulk_update(update_data_list)

            return {
                "data": await self._return_multi_data(items),
                "message": f"Successfully updated {len(items)} items",
            }
        except exceptions.ValidationException:
            raise
        except Exception as e:
            raise exceptions.ServiceException(
                detail=f"Error in bulk creating items: {str(e)}"
            ) from e

    async def search(self, query: str):
        """Search items based on query string."""
        try:
            if not self.repository._search_fields:
                raise exceptions.ServiceException(
                    detail="Search fields not defined in repository"
                )
            result = await self.repository.search(query, self.repository._search_fields)
            return await self._result_to_pagenation_response(result)
        except Exception as e:
            raise exceptions.ServiceException(
                detail=f"Error searching items: {str(e)}"
            ) from e

    # Validation methods to be overridden by subclasses
    async def _validate_create(self, create_data: Dict[str, Any]) -> None:
        """Validate data before creation. Override in subclasses."""
        pass

    async def _validate_update(
        self, item_id: Any, update_data: Dict[str, Any], existing_item: T
    ) -> None:
        """Validate data before update. Override in subclasses."""
        pass

    async def _validate_delete(self, item_id: Any, existing_item: T) -> None:
        """Validate before soft delete. Override in subclasses."""
        pass

    async def _validate_force_delete(self, item_id: Any, existing_item: T) -> None:
        """Validate before force delete. Override in subclasses."""
        pass

    async def _result_to_pagenation_response(self, result: PaginatedResponse) -> dict:
        return {
            "items": await self._return_multi_data(result.data),
            "total": result.total,
            "page": result.page,
            "per_page": result.per_page,
            "pages": result.pages,
            "message": result.message,
        }
