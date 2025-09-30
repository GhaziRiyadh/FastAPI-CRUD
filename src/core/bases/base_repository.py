from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlmodel import SQLModel, func, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import BaseModel

from src.core.response import schemas

T = TypeVar("T", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class RepositoryError(Exception):
    """Custom exception for repository errors."""

    pass


class BaseRepository(Generic[T]):
    model: Type[T]

    def __init__(self, get_session: Callable[..., AsyncSession]):
        self.get_session = get_session

    def _handle_db_error(self, error: SQLAlchemyError, operation: str) -> None:
        """Handle database errors and raise appropriate exceptions."""
        if isinstance(error, IntegrityError):
            raise RepositoryError(
                f"Database integrity error during {operation}: {error}"
            ) from error
        else:
            raise RepositoryError(
                f"Database error during {operation}: {error}"
            ) from error

    def _build_select_stmt(self, include_deleted: bool = False, **filters) -> Any:
        """Build select statement with optional filters and soft delete handling."""
        stmt = select(self.model)

        # Apply soft delete filter if applicable
        if not include_deleted and hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)  # type: ignore

        # Apply additional filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)

        return stmt

    # ----------------- CRUD ----------------- #
    async def get(
        self, item_id: Any, include_deleted: bool = False, **filters
    ) -> Optional[T]:
        """Get a single item by ID with optional additional filters."""
        async with self.get_session() as db:
            try:
                stmt = self._build_select_stmt(
                    include_deleted=include_deleted, **filters
                )
                stmt = stmt.where(self.model.id == item_id)  # type: ignore

                result = await db.exec(stmt)
                return result.first()
            except SQLAlchemyError as e:
                self._handle_db_error(e, "get")

    async def get_one(self, **filters) -> Optional[T]:
        """Get a single item matching the filters."""
        async with self.get_session() as db:
            try:
                stmt = self._build_select_stmt(**filters)
                result = await db.exec(stmt)
                return result.first()
            except SQLAlchemyError as e:
                self._handle_db_error(e, "get_one")

    async def get_many(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        **filters,
    ) -> List[T]:  # type:ignore
        """Get multiple items with filtering and pagination."""
        async with self.get_session() as db:
            try:
                stmt = self._build_select_stmt(
                    include_deleted=include_deleted, **filters
                )
                stmt = stmt.offset(skip).limit(limit)

                result = await db.exec(stmt)
                return result.all()
            except SQLAlchemyError as e:
                self._handle_db_error(e, "get_many")

    async def list(
        self,
        page: int = 1,
        per_page: int = 10,
        include_deleted: bool = False,
        **filters,
    ) -> schemas.PaginatedResponse:  # type:ignore
        """Get paginated list of items."""
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10

        async with self.get_session() as db:
            try:
                offset = (page - 1) * per_page

                # Build base query
                stmt = self._build_select_stmt(
                    include_deleted=include_deleted, **filters
                )

                # Get total count
                count_stmt = select(func.count()).select_from(stmt.subquery())
                total_result = await db.exec(count_stmt)
                total = total_result.one()

                # Get paginated items
                result = await db.exec(stmt.offset(offset).limit(per_page))
                items = result.all()

                # Calculate pages
                pages = (total + per_page - 1) // per_page  # Ceiling division

                return schemas.PaginatedResponse(
                    success=True,
                    data=items,
                    total=total,
                    page=page,
                    per_page=per_page,
                    pages=pages,
                    message="Items retrieved successfully",
                )
            except SQLAlchemyError as e:
                self._handle_db_error(e, "list")

    async def create(
        self, obj_in: Union[Dict[str, Any], BaseModel]
    ) -> T:  # type:ignore
        """Create a new item."""
        if isinstance(obj_in, BaseModel):
            obj_in = obj_in.model_dump(exclude_unset=True)

        async with self.get_session() as db:
            try:
                obj = self.model(**obj_in)  # type: ignore
                db.add(obj)
                await db.commit()
                await db.refresh(obj)
                return obj
            except IntegrityError as e:
                await db.rollback()
                self._handle_db_error(e, "create")
            except SQLAlchemyError as e:
                await db.rollback()
                self._handle_db_error(e, "create")

    async def create_many(
        self, objects_in: List[Union[Dict[str, Any], BaseModel]]
    ) -> List[T]:  # type:ignore
        """Create multiple items at once."""
        objects_data = [
            obj.model_dump(exclude_unset=True) if isinstance(obj, BaseModel) else obj
            for obj in objects_in
        ]

        async with self.get_session() as db:
            try:
                objects = [self.model(**data) for data in objects_data]  # type: ignore
                db.add_all(objects)
                await db.commit()

                # Refresh all objects
                for obj in objects:
                    await db.refresh(obj)

                return objects
            except SQLAlchemyError as e:
                await db.rollback()
                self._handle_db_error(e, "create_many")

    async def update(
        self,
        item_id: Any,
        obj_in: Union[Dict[str, Any], BaseModel],
        exclude_unset: bool = True,
    ) -> Optional[T]:
        """Update an existing item."""
        if isinstance(obj_in, BaseModel):
            update_data = obj_in.model_dump(exclude_unset=exclude_unset)
        else:
            update_data = obj_in

        # Remove ID from update data to prevent changing primary key
        update_data.pop("id", None)

        if not update_data:
            raise RepositoryError("No data provided for update")

        async with self.get_session() as db:
            try:
                db_obj = await db.get(self.model, item_id)
                if not db_obj:
                    return None

                for key, value in update_data.items():
                    if hasattr(db_obj, key) and key != "id":
                        setattr(db_obj, key, value)

                await db.commit()
                await db.refresh(db_obj)
                return db_obj
            except SQLAlchemyError as e:
                await db.rollback()
                self._handle_db_error(e, "update")

    async def exists(
        self, item_id: Any, include_deleted: bool = False
    ) -> bool:  # type:ignore
        """Check if an item exists."""
        async with self.get_session() as db:
            try:
                stmt = select(self.model.id).where(self.model.id == item_id)  # type: ignore
                if not include_deleted and hasattr(self.model, "is_deleted"):
                    stmt = stmt.where(self.model.is_deleted == False)  # type: ignore

                result = await db.exec(stmt)
                return result.first() is not None
            except SQLAlchemyError as e:
                self._handle_db_error(e, "exists")

    async def count(
        self, include_deleted: bool = False, **filters
    ) -> int:  # type:ignore
        """Count items matching optional filters."""
        async with self.get_session() as db:
            try:
                stmt = self._build_select_stmt(
                    include_deleted=include_deleted, **filters
                )
                count_stmt = select(func.count()).select_from(stmt.subquery())
                result = await db.exec(count_stmt)
                return result.one()
            except SQLAlchemyError as e:
                self._handle_db_error(e, "count")

    # ----------------- DELETE / RESTORE ----------------- #
    async def soft_delete(self, item_id: Any) -> bool:  # type:ignore
        """Mark item as deleted instead of removing it."""
        if not hasattr(self.model, "is_deleted"):
            raise AttributeError("Model must have 'is_deleted' field for soft delete")

        async with self.get_session() as db:
            try:
                db_obj = await db.get(self.model, item_id)
                if not db_obj:
                    return False

                setattr(db_obj, "is_deleted", True)
                await db.commit()
                return True
            except SQLAlchemyError as e:
                await db.rollback()
                self._handle_db_error(e, "soft_delete")

    async def restore(self, item_id: Any) -> bool:  # type:ignore
        """Restore a soft deleted item."""
        if not hasattr(self.model, "is_deleted"):
            raise AttributeError("Model must have 'is_deleted' field for restore")

        async with self.get_session() as db:
            try:
                db_obj = await db.get(self.model, item_id)
                if not db_obj:
                    return False

                setattr(db_obj, "is_deleted", False)
                await db.commit()
                return True
            except SQLAlchemyError as e:
                await db.rollback()
                self._handle_db_error(e, "restore")

    async def force_delete(self, item_id: Any) -> bool:  # type:ignore
        """Permanently delete the item from DB."""
        async with self.get_session() as db:
            try:
                db_obj = await db.get(self.model, item_id)
                if not db_obj:
                    return False

                await db.delete(db_obj)
                await db.commit()
                return True
            except SQLAlchemyError as e:
                await db.rollback()
                self._handle_db_error(e, "force_delete")

    async def force_delete_many(self, item_ids: List[Any]) -> bool:  # type:ignore
        """Permanently delete multiple items from DB."""
        async with self.get_session() as db:
            try:
                result = await db.exec(
                    select(self.model).where(self.model.id.in_(item_ids))  # type: ignore
                )
                objects = result.all()

                for obj in objects:
                    await db.delete(obj)

                await db.commit()
                return True
            except SQLAlchemyError as e:
                await db.rollback()
                self._handle_db_error(e, "force_delete_many")
