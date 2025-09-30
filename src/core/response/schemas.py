from fastapi import Query
from pydantic import BaseModel, Field
from typing import Generic, List, TypeVar, Optional

from sqlmodel import SQLModel

T = TypeVar("T", bound=SQLModel)


class BaseResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = Field(default=None)
    data: Optional[T] = None


class PaginatedResponse(BaseResponse, Generic[T]):
    total: int = Field(default=0)
    page: int = Field(default=1)
    per_page: int = Field(default=100)
    pages: int = Field(default=1)
    data: List[T] = []


class ErrorDetail(BaseModel):
    field:str = ""
    code: str = Field(default="ERROR")
    message: str = Field(default="Unknown Error")
    target: Optional[str] = Field(default=None)


class ErrorResponse(BaseResponse):
    success: bool = Field(default=False)
    error_code: str = Field(default="ERROR")
    error_details: list[ErrorDetail] = Field(default=[])


class PaginationSchema(BaseModel):
    page: int = Query(1, ge=1)
    per_page: int = Query(10, ge=1, le=100)
