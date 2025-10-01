from fastapi import Query
from pydantic import BaseModel, Field
from typing import Any, List, Optional


class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = Field(default=None)
    data: Any = None


class PaginatedResponse(BaseResponse):
    total: int = Field(default=0)
    page: int = Field(default=1)
    per_page: int = Field(default=100)
    pages: int = Field(default=1)
    data: List[Any] = []


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
