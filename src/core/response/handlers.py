from typing import Any
from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from jwt import ExpiredSignatureError
from sqlmodel import SQLModel

from .. import exceptions

from . import schemas


def success_response(
    data: Any = None,
    message: str = "Operation successful",
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    """Return a successful response."""
    if isinstance(data,SQLModel):
        data = data.model_dump()
    response = schemas.BaseResponse(success=True, message=message, data=data)
    return JSONResponse(content=jsonable_encoder(response), status_code=status_code)


def paginated_response(
    items: Any,
    total: int,
    page: int,
    per_page: int,
    pages: int,
    message: str = "Data retrieved successfully",
) -> JSONResponse:
    """Return a paginated response."""
    response = schemas.PaginatedResponse(
        success=True,
        message=message,
        total=total,
        page=page,
        per_page=per_page,
        data=items,
        pages=pages,
    )
    return JSONResponse(content=jsonable_encoder(response.__dict__), status_code=status.HTTP_200_OK)


def error_response(
    error_code: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: list[dict] = [],
) -> JSONResponse:
    """Return an error response."""
    error_details = [schemas.ErrorDetail(**detail) for detail in (details or [])]

    response = schemas.ErrorResponse(
        success=False,
        error_code=error_code,
        message=message,
        error_details=error_details,
    )
    return JSONResponse(content=response.model_dump(), status_code=status_code)


def exception_to_error_response(exception: exceptions.BaseAPIException) -> JSONResponse:
    """Convert an exception to an error response."""
    return error_response(
        error_code=exception.error_code,
        message=exception.detail,
        status_code=exception.status_code,
        details=[detail.model_dump() for detail in exception.error_details]
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for the application."""
    
    # Handle our custom API exceptions
    if isinstance(exc, exceptions.BaseAPIException):
        return exception_to_error_response(exc)
    
    # Handle FastAPI's validation errors
    elif isinstance(exc, RequestValidationError):
        error_details = [
            schemas.ErrorDetail(
                field=" -> ".join([str(loc) for loc in error["loc"]]),
                message=error["msg"],
                code="VALIDATION_ERROR"
            )
            for error in exc.errors()
        ]
        return error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=[detail.model_dump() for detail in error_details]
        )
    
    # Handle JWT token expiration
    elif isinstance(exc, ExpiredSignatureError):
        return error_response(
            error_code="EXPIRED_TOKEN",
            message="Authentication token has expired",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Handle generic unexpected errors
    else:
        # Log the unexpected error here
        # logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        
        return error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )