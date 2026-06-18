from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DashboardStats(BaseModel):
    total_users: int
    total_news: int
    total_views: int
    total_categories: int
    model_config = ConfigDict(from_attributes=True)


# --- User Management ---
class AdminUserInfo(BaseModel):
    id: int
    username: str
    nickname: Optional[str] = None
    role: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class AdminUserUpdate(BaseModel):
    nickname: Optional[str] = None
    role: Optional[str] = None


class AdminUserListResponse(BaseModel):
    list: list[AdminUserInfo]
    total: int
    page: int
    pageSize: int


# --- News Management ---
class AdminNewsCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content: str = Field(..., min_length=1)
    image: Optional[str] = None
    author: Optional[str] = None
    category_id: int = Field(..., alias="categoryId")
    publish_time: Optional[datetime] = None
    source_url: Optional[str] = Field(None, alias="sourceUrl")

    model_config = ConfigDict(populate_by_name=True)


class AdminNewsUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = None
    image: Optional[str] = None
    author: Optional[str] = None
    category_id: Optional[int] = Field(None, alias="categoryId")
    publish_time: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)


class AdminNewsInfo(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    content: str
    image: Optional[str] = None
    author: Optional[str] = None
    category_id: int
    views: int
    status: str = "published"
    source_url: Optional[str] = None
    publish_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class AdminNewsListResponse(BaseModel):
    list: list[AdminNewsInfo]
    total: int
    page: int
    pageSize: int


# --- Category Management ---
class AdminCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sort_order: int = Field(0, alias="sortOrder")


class AdminCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sort_order: Optional[int] = Field(None, alias="sortOrder")

    model_config = ConfigDict(populate_by_name=True)


# --- Batch Import ---
class ImportNewsItem(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    content: Optional[str] = ""
    author: Optional[str] = ""
    sourceUrl: Optional[str] = None
    image: Optional[str] = ""
    publishTime: Optional[str] = None
    categoryId: int
    keywords: Optional[str] = ""


class ImportResult(BaseModel):
    total: int
    imported: int
    skipped: int
    errors: list[str]


# --- Category Management ---
class AdminCategoryInfo(BaseModel):
    id: int
    name: str
    sort_order: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
