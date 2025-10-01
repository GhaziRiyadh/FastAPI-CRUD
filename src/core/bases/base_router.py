from typing import Any, Callable, Dict, List, Optional, Type, get_type_hints
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, create_model

from src.core.bases.base_service import BaseService
from src.core.response.handlers import success_response, paginated_response, error_response
from src.core import exceptions
from src.core.schemas.fields import DynamicFormConfig, ModelDefinition
from src.core.services.field_service import FieldService


# Schema type definitions for dynamic model creation
class CreateSchema(BaseModel):
    pass


class UpdateSchema(BaseModel):
    pass


class QueryParams(BaseModel):
    page: int = Query(1, ge=1, description="Page number")
    per_page: int = Query(10, ge=1, le=100, description="Items per page")
    include_deleted: bool = Query(False, description="Include soft deleted items")


class BaseRouter:
    """Base router class with automatic CRUD endpoints."""
    
    def __init__(
        self,
        service: BaseService,
        tags: Optional[List[str]] = None,
        prefix: str = "",
        create_schema: Optional[Type[BaseModel]] = None,
        update_schema: Optional[Type[BaseModel]] = None,
        response_schema: Optional[Type[BaseModel]] = None,
        dependencies: Optional[List[Callable]] = None
    ):
        self.service = service
        self.tags = tags or [self.__class__.__name__.replace("Router", "")]
        self.prefix = prefix
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.response_schema = response_schema
        
        # Create router
        self.router = APIRouter(
            prefix=self.prefix,
            tags=self.tags, #type:ignore
            dependencies=dependencies or [] #type:ignore
        )
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self) -> None:
        """Register all CRUD routes."""
        self._register_get_by_id()
        self._register_list()
        self._register_create()
        self._register_update()
        self._register_soft_delete()
        self._register_restore()
        self._register_force_delete()
        self._register_count()
        self._register_exists()
        self._register_field_routes()
    
    def _register_get_by_id(self) -> None:
        """Register GET /{item_id} route."""
        @self.router.get(
            "/{item_id}",
            response_model=None,  # We'll use response handlers instead
            summary="Get item by ID",
            responses={
                200: {"description": "Item retrieved successfully"},
                404: {"description": "Item not found"},
                500: {"description": "Internal server error"}
            }
        )
        async def get_by_id(
            item_id: int,
            include_deleted: bool = Query(False, description="Include soft deleted items")
        ):
            try:
                result = await self.service.get_by_id(
                    item_id=item_id,
                    include_deleted=include_deleted
                )
                return success_response(
                    data=result["data"],
                    message=result["message"]
                )
            except exceptions.NotFoundException as e:
                return error_response(
                    error_code="NOT_FOUND",
                    message=str(e.detail),
                    status_code=status.HTTP_404_NOT_FOUND
                )
            except exceptions.ServiceException as e:
                return error_response(
                    error_code="SERVICE_ERROR",
                    message=str(e.detail),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    def _register_list(self) -> None:
        """Register GET / route with pagination."""
        @self.router.get(
            "/",
            summary="List items",
            responses={
                200: {"description": "Items retrieved successfully"},
                500: {"description": "Internal server error"}
            }
        )
        async def list_items(
            page: int = Query(1, ge=1),
            per_page: int = Query(10, ge=1, le=100),
            include_deleted: bool = Query(False),
            # Additional filters can be added here
        ):
            try:
                result = await self.service.get_list(
                    page=page,
                    per_page=per_page,
                    include_deleted=include_deleted
                )
                return paginated_response(
                    items=result["items"],
                    total=result["total"],
                    page=result["page"],
                    per_page=result["per_page"],
                    pages=result["pages"],
                    message=result["message"]
                )
            except exceptions.ServiceException as e:
                return error_response(
                    error_code="SERVICE_ERROR",
                    message=str(e.detail),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    def _register_create(self) -> None:
        """Register POST / route."""
        if not self.create_schema:
            return
            
        @self.router.post(
            "/",
            status_code=status.HTTP_201_CREATED,
            summary="Create new item",
            responses={
                201: {"description": "Item created successfully"},
                400: {"description": "Bad request"},
                422: {"description": "Validation error"},
                500: {"description": "Internal server error"}
            }
        )
        async def create_item(
            item_data: self.create_schema,  # type: ignore
            request: Request
        ):
            try:
                result = await self.service.create(item_data)
                return success_response(
                    data=result["data"],
                    message=result["message"],
                    status_code=status.HTTP_201_CREATED
                )
            except exceptions.ValidationException as e:
                return error_response(
                    error_code="VALIDATION_ERROR",
                    message=str(e.detail),
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    details=[detail.model_dump() for detail in e.error_details]
                )
            except exceptions.ConflictException as e:
                return error_response(
                    error_code="CONFLICT",
                    message=str(e.detail),
                    status_code=status.HTTP_409_CONFLICT,
                    details=[detail.model_dump() for detail in e.error_details]
                )
            except exceptions.ServiceException as e:
                return error_response(
                    error_code="SERVICE_ERROR",
                    message=str(e.detail),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    def _register_update(self) -> None:
        """Register PUT /{item_id} route."""
        if not self.update_schema:
            return
            
        @self.router.put(
            "/{item_id}",
            summary="Update item",
            responses={
                200: {"description": "Item updated successfully"},
                404: {"description": "Item not found"},
                422: {"description": "Validation error"},
                500: {"description": "Internal server error"}
            }
        )
        async def update_item(
            item_id: int,
            item_data: self.update_schema  # type: ignore
        ):
            try:
                result = await self.service.update(item_id, item_data)
                return success_response(
                    data=result["data"],
                    message=result["message"]
                )
            except exceptions.NotFoundException as e:
                return error_response(
                    error_code="NOT_FOUND",
                    message=str(e.detail),
                    status_code=status.HTTP_404_NOT_FOUND
                )
            except exceptions.ValidationException as e:
                return error_response(
                    error_code="VALIDATION_ERROR",
                    message=str(e.detail),
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    details=[detail.model_dump() for detail in e.error_details]
                )
            except exceptions.ServiceException as e:
                return error_response(
                    error_code="SERVICE_ERROR",
                    message=str(e.detail),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    def _register_soft_delete(self) -> None:
        """Register DELETE /{item_id} route (soft delete)."""
        @self.router.delete(
            "/{item_id}",
            summary="Soft delete item",
            responses={
                200: {"description": "Item soft deleted successfully"},
                404: {"description": "Item not found"},
                500: {"description": "Internal server error"}
            }
        )
        async def soft_delete_item(item_id: int):
            try:
                result = await self.service.soft_delete(item_id)
                return success_response(
                    data=result["data"],
                    message=result["message"]
                )
            except exceptions.NotFoundException as e:
                return error_response(
                    error_code="NOT_FOUND",
                    message=str(e.detail),
                    status_code=status.HTTP_404_NOT_FOUND
                )
            except exceptions.ServiceException as e:
                return error_response(
                    error_code="SERVICE_ERROR",
                    message=str(e.detail),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    def _register_restore(self) -> None:
        """Register PATCH /{item_id}/restore route."""
        @self.router.patch(
            "/{item_id}/restore",
            summary="Restore soft deleted item",
            responses={
                200: {"description": "Item restored successfully"},
                404: {"description": "Item not found"},
                500: {"description": "Internal server error"}
            }
        )
        async def restore_item(item_id: int):
            try:
                result = await self.service.restore(item_id)
                return success_response(
                    data=result["data"],
                    message=result["message"]
                )
            except exceptions.NotFoundException as e:
                return error_response(
                    error_code="NOT_FOUND",
                    message=str(e.detail),
                    status_code=status.HTTP_404_NOT_FOUND
                )
            except exceptions.ServiceException as e:
                return error_response(
                    error_code="SERVICE_ERROR",
                    message=str(e.detail),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    def _register_force_delete(self) -> None:
        """Register DELETE /{item_id}/force route (permanent delete)."""
        @self.router.delete(
            "/{item_id}/force",
            summary="Permanently delete item",
            responses={
                200: {"description": "Item permanently deleted successfully"},
                404: {"description": "Item not found"},
                500: {"description": "Internal server error"}
            }
        )
        async def force_delete_item(item_id: int):
            try:
                result = await self.service.force_delete(item_id)
                return success_response(
                    data=result["data"],
                    message=result["message"]
                )
            except exceptions.NotFoundException as e:
                return error_response(
                    error_code="NOT_FOUND",
                    message=str(e.detail),
                    status_code=status.HTTP_404_NOT_FOUND
                )
            except exceptions.ServiceException as e:
                return error_response(
                    error_code="SERVICE_ERROR",
                    message=str(e.detail),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    def _register_count(self) -> None:
        """Register GET /count route."""
        @self.router.get(
            "/count",
            summary="Count items",
            responses={
                200: {"description": "Count retrieved successfully"},
                500: {"description": "Internal server error"}
            }
        )
        async def count_items(
            include_deleted: bool = Query(False)
        ):
            try:
                result = await self.service.count(include_deleted=include_deleted)
                return success_response(
                    data=result["data"],
                    message=result["message"]
                )
            except exceptions.ServiceException as e:
                return error_response(
                    error_code="SERVICE_ERROR",
                    message=str(e.detail),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    def _register_exists(self) -> None:
        """Register GET /{item_id}/exists route."""
        @self.router.get(
            "/{item_id}/exists",
            summary="Check if item exists",
            responses={
                200: {"description": "Existence check completed"},
                500: {"description": "Internal server error"}
            }
        )
        async def check_exists(
            item_id: int,
            include_deleted: bool = Query(False)
        ):
            try:
                result = await self.service.exists(
                    item_id=item_id,
                    include_deleted=include_deleted
                )
                return success_response(
                    data=result["data"],
                    message=result["message"]
                )
            except exceptions.ServiceException as e:
                return error_response(
                    error_code="SERVICE_ERROR",
                    message=str(e.detail),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    # Additional utility methods for custom routes
    def add_custom_route(
        self,
        path: str,
        method: str,
        endpoint: Callable,
        **kwargs
    ) -> None:
        """Add a custom route to the router."""
        method = method.lower()
        router_method = getattr(self.router, method, None)
        
        if router_method:
            router_method(path, **kwargs)(endpoint)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    
    def include_router(self, router: APIRouter, **kwargs) -> None:
        """Include another router in this router."""
        self.router.include_router(router, **kwargs)
    
    def get_router(self) -> APIRouter:
        """Get the FastAPI router instance."""
        return self.router
    
    def _register_field_routes(self):
        """Register dynamic field definition routes."""
        
        @self.router.get(
            "/model/fields",
            summary="Get model field definitions",
            response_model=ModelDefinition
        )
        async def get_model_fields():
            """Get complete field definitions for dynamic frontend."""
            try:
                model_class = self.service.repository.model
                field_def = FieldService.get_model_definition(model_class)
                return success_response(
                    data=field_def.model_dump(),
                    message=f"Field definitions for {model_class.__name__} retrieved successfully"
                )
            except Exception as e:
                return error_response(
                    error_code="FIELD_DEFINITION_ERROR",
                    message=f"Error retrieving field definitions: {str(e)}",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        @self.router.get(
            "/model/form-config",
            summary="Get dynamic form configuration",
            response_model=DynamicFormConfig
        )
        async def get_form_config():
            """Get form configuration for dynamic frontend forms."""
            try:
                model_class = self.service.repository.model
                form_config = FieldService.get_dynamic_form_config(model_class)
                return success_response(
                    data=form_config.model_dump(),
                    message=f"Form configuration for {model_class.__name__} retrieved successfully"
                )
            except Exception as e:
                return error_response(
                    error_code="FORM_CONFIG_ERROR",
                    message=f"Error retrieving form configuration: {str(e)}",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        @self.router.get(
            "/model/schemas",
            summary="Get model schemas for frontend"
        )
        async def get_model_schemas():
            """Get create and update schemas for frontend validation."""
            try:
                model_class = self.service.repository.model
                model_def = FieldService.get_model_definition(model_class)
                
                # Generate schema definitions
                create_schema = {}
                update_schema = {}
                
                for field in model_def.fields:
                    # Skip internal fields in create/update schemas
                    if field.name in ['id', 'created_at', 'updated_at', 'is_deleted']:
                        continue
                    
                    field_def = {
                        'type': field.type.value,
                        'required': field.is_required and field.name not in ['id', 'created_at', 'updated_at']
                    }
                    
                    if field.default_value is not None:
                        field_def['default'] = field.default_value
                    
                    # Create schema (all required fields)
                    create_schema[field.name] = field_def
                    
                    # Update schema (all fields optional)
                    update_field_def = field_def.copy()
                    update_field_def['required'] = False
                    update_schema[field.name] = update_field_def
                
                schemas = {
                    'create_schema': create_schema,
                    'update_schema': update_schema,
                    'model_name': model_def.model_name
                }
                
                return success_response(
                    data=schemas,
                    message=f"Schemas for {model_def.model_name} retrieved successfully"
                )
            except Exception as e:
                return error_response(
                    error_code="SCHEMA_ERROR",
                    message=f"Error retrieving schemas: {str(e)}",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )