from pydantic import BaseModel
from typing import Optional, List

class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None

class CategoryResponseBase(CategoryBase):
    id: int

    class Config:
        from_attributes = True

# We need a separate model to include subcategories to avoid recursion issues if not careful,
# or we can use ForwardRef.

class CategoryResponse(CategoryResponseBase):
    subcategories: List['CategoryResponse'] = []

    class Config:
        from_attributes = True
