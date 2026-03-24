"""
Base response and error schemas.

Use these as return types in router functions to enforce a consistent
API envelope across all endpoints.

Success:
    { "success": true, "data": <T> }

Error (produced by exception_handler.py):
    { "success": false, "error": { "code": int, "message": str, "detail": any } }

Paginated:
    { "success": true, "data": { "items": [...], "total": int, "page": int,
                                  "limit": int, "pages": int } }
"""

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: int
    message: str
    detail: Optional[object] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T


class PaginatedData(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: PaginatedData[T]
