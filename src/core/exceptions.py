from typing import Any, Dict, List, Optional, Union
from fastapi import status
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Detail structure for error responses."""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class BaseAPIException(Exception):
    """Base exception for all API exceptions."""
    
    def __init__(
        self,
        detail: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        error_details: Optional[List[ErrorDetail]] = None
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        self.error_details = error_details or []
        super().__init__(self.detail)


# 400 Bad Request Exceptions
class BadRequestException(BaseAPIException):
    """Raised when the request is malformed or invalid."""
    
    def __init__(
        self,
        detail: str = "Bad request",
        error_code: str = "BAD_REQUEST",
        error_details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            error_details=error_details
        )


class ValidationException(BaseAPIException):
    """Raised when data validation fails."""
    
    def __init__(
        self,
        detail: str = "Validation error",
        error_code: str = "VALIDATION_ERROR",
        error_details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            error_details=error_details
        )


class InvalidInputException(BadRequestException):
    """Raised when input data is invalid."""
    
    def __init__(
        self,
        detail: str = "Invalid input data",
        error_code: str = "INVALID_INPUT",
        error_details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            detail=detail,
            error_code=error_code,
            error_details=error_details
        )


class MissingRequiredFieldException(ValidationException):
    """Raised when required fields are missing."""
    
    def __init__(
        self,
        field: str,
        detail: Optional[str] = None,
        error_code: str = "MISSING_REQUIRED_FIELD"
    ):
        if not detail:
            detail = f"Required field '{field}' is missing"
        
        error_details = [ErrorDetail(field=field, message=detail, code=error_code)]
        super().__init__(
            detail=detail,
            error_code=error_code,
            error_details=error_details
        )


# 401 Unauthorized Exceptions
class UnauthorizedException(BaseAPIException):
    """Raised when authentication is required but not provided or invalid."""
    
    def __init__(
        self,
        detail: str = "Authentication required",
        error_code: str = "UNAUTHORIZED",
        error_details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            error_details=error_details
        )


class InvalidTokenException(UnauthorizedException):
    """Raised when provided token is invalid."""
    
    def __init__(
        self,
        detail: str = "Invalid authentication token",
        error_code: str = "INVALID_TOKEN"
    ):
        super().__init__(detail=detail, error_code=error_code)


class ExpiredTokenException(UnauthorizedException):
    """Raised when provided token has expired."""
    
    def __init__(
        self,
        detail: str = "Authentication token has expired",
        error_code: str = "EXPIRED_TOKEN"
    ):
        super().__init__(detail=detail, error_code=error_code)


# 403 Forbidden Exceptions
class ForbiddenException(BaseAPIException):
    """Raised when user doesn't have permission to access the resource."""
    
    def __init__(
        self,
        detail: str = "Access forbidden",
        error_code: str = "FORBIDDEN",
        error_details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            error_details=error_details
        )


class InsufficientPermissionsException(ForbiddenException):
    """Raised when user lacks specific permissions."""
    
    def __init__(
        self,
        required_permissions: List[str],
        detail: Optional[str] = None,
        error_code: str = "INSUFFICIENT_PERMISSIONS"
    ):
        if not detail:
            detail = f"Insufficient permissions. Required: {', '.join(required_permissions)}"
        
        super().__init__(detail=detail, error_code=error_code)


# 404 Not Found Exceptions
class NotFoundException(BaseAPIException):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        detail: str = "Resource not found",
        error_code: str = "NOT_FOUND",
        error_details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
            error_details=error_details
        )


class ResourceNotFoundException(NotFoundException):
    """Raised when a specific resource is not found."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Any,
        detail: Optional[str] = None,
        error_code: str = "RESOURCE_NOT_FOUND"
    ):
        if not detail:
            detail = f"{resource_type} with id {resource_id} not found"
        
        super().__init__(detail=detail, error_code=error_code)


# 409 Conflict Exceptions
class ConflictException(BaseAPIException):
    """Raised when there's a conflict with the current state."""
    
    def __init__(
        self,
        detail: str = "Conflict occurred",
        error_code: str = "CONFLICT",
        error_details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
            error_details=error_details
        )


class DuplicateEntryException(ConflictException):
    """Raised when trying to create a duplicate resource."""
    
    def __init__(
        self,
        resource_type: str,
        field: str,
        value: Any,
        detail: Optional[str] = None,
        error_code: str = "DUPLICATE_ENTRY"
    ):
        if not detail:
            detail = f"{resource_type} with {field} '{value}' already exists"
        
        error_details = [
            ErrorDetail(field=field, message=f"Value '{value}' already exists", code=error_code)
        ]
        super().__init__(detail=detail, error_code=error_code, error_details=error_details)


class OperationNotAllowedException(ConflictException):
    """Raised when an operation is not allowed in current state."""
    
    def __init__(
        self,
        detail: str = "Operation not allowed",
        error_code: str = "OPERATION_NOT_ALLOWED",
        error_details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(detail=detail, error_code=error_code, error_details=error_details)


# 422 Unprocessable Entity Exceptions
class UnprocessableEntityException(BaseAPIException):
    """Raised when the request is well-formed but cannot be processed."""
    
    def __init__(
        self,
        detail: str = "Unprocessable entity",
        error_code: str = "UNPROCESSABLE_ENTITY",
        error_details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            error_details=error_details
        )


# 429 Too Many Requests Exceptions
class RateLimitException(BaseAPIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        error_code: str = "RATE_LIMIT_EXCEEDED",
        retry_after: Optional[int] = None
    ):
        self.retry_after = retry_after
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code=error_code
        )


# 500 Internal Server Error Exceptions
class ServiceException(BaseAPIException):
    """Raised when an internal service error occurs."""
    
    def __init__(
        self,
        detail: str = "Internal service error",
        error_code: str = "SERVICE_ERROR",
        error_details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            error_details=error_details
        )


class DatabaseException(ServiceException):
    """Raised when a database operation fails."""
    
    def __init__(
        self,
        detail: str = "Database operation failed",
        error_code: str = "DATABASE_ERROR"
    ):
        super().__init__(detail=detail, error_code=error_code)


class ExternalServiceException(ServiceException):
    """Raised when an external service call fails."""
    
    def __init__(
        self,
        service_name: str,
        detail: Optional[str] = None,
        error_code: str = "EXTERNAL_SERVICE_ERROR"
    ):
        if not detail:
            detail = f"External service '{service_name}' is unavailable"
        
        super().__init__(detail=detail, error_code=error_code)


class OperationException(ServiceException):
    """Raised when an operation fails unexpectedly."""
    
    def __init__(
        self,
        detail: str = "Operation failed",
        error_code: str = "OPERATION_FAILED"
    ):
        super().__init__(detail=detail, error_code=error_code)


# Repository-specific exceptions
class RepositoryException(ServiceException):
    """Base exception for repository layer errors."""
    
    def __init__(
        self,
        detail: str = "Repository error occurred",
        error_code: str = "REPOSITORY_ERROR"
    ):
        super().__init__(detail=detail, error_code=error_code)


class ObjectNotFoundException(RepositoryException, NotFoundException):
    """Raised when an object is not found in the repository."""
    
    def __init__(
        self,
        model_name: str,
        object_id: Any,
        detail: Optional[str] = None,
        error_code: str = "OBJECT_NOT_FOUND"
    ):
        if not detail:
            detail = f"{model_name} with id {object_id} not found"
        
        super().__init__(detail=detail, error_code=error_code)


class IntegrityViolationException(RepositoryException, ConflictException):
    """Raised when a database integrity constraint is violated."""
    
    def __init__(
        self,
        detail: str = "Database integrity constraint violated",
        error_code: str = "INTEGRITY_VIOLATION"
    ):
        super().__init__(detail=detail, error_code=error_code)


# Business logic exceptions
class BusinessRuleException(BaseAPIException):
    """Raised when a business rule is violated."""
    
    def __init__(
        self,
        detail: str = "Business rule violation",
        error_code: str = "BUSINESS_RULE_VIOLATION",
        error_details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            error_details=error_details
        )


class StateTransitionException(BusinessRuleException):
    """Raised when an invalid state transition is attempted."""
    
    def __init__(
        self,
        current_state: str,
        target_state: str,
        detail: Optional[str] = None,
        error_code: str = "INVALID_STATE_TRANSITION"
    ):
        if not detail:
            detail = f"Invalid state transition from '{current_state}' to '{target_state}'"
        
        super().__init__(detail=detail, error_code=error_code)


# Utility functions for working with exceptions
def create_validation_errors(field_errors: Dict[str, str]) -> List[ErrorDetail]:
    """Create ErrorDetail list from field validation errors."""
    return [
        ErrorDetail(field=field, message=message, code="VALIDATION_ERROR")
        for field, message in field_errors.items()
    ]


def format_exception_response(exception: BaseAPIException) -> Dict[str, Any]:
    """Format exception for JSON response."""
    response = {
        "success": False,
        "error_code": exception.error_code,
        "message": exception.detail,
    }
    
    if exception.error_details:
        response["error_details"] = [
            detail.dict() for detail in exception.error_details
        ]
    
    return response