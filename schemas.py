"""
schemas.py
==========
Pydantic data validation schemas for ExpensePulse API endpoints.
Provides type safety, automatic coercion, boundary checks, and friendly validation errors.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class BaseFilterSchema(BaseModel):
    """Common filtering parameters used across filter, export, and analysis endpoints."""
    model_config = ConfigDict(extra="ignore")

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    year_months: Optional[List[str]] = None
    accounts: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    category_groups: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    types: Optional[List[str]] = None
    spending_nature: str = "all"
    weekend_filter: str = "all"
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    search_query: Optional[str] = None
    include_transfers: bool = False

    @field_validator("start_date", "end_date", "search_query", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v is not None and isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("min_amount", "max_amount", mode="before")
    @classmethod
    def parse_optional_amount(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return float(v)

    @field_validator("year_months", "accounts", "categories", "category_groups", "labels", "types", mode="before")
    @classmethod
    def empty_list_or_none(cls, v):
        if v is None:
            return None
        if isinstance(v, list) and len(v) == 0:
            return None
        return v


class FilterRequestSchema(BaseFilterSchema):
    """Schema for POST /api/filter including pagination, sorting, and selected label."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=200)
    sort_by: str = "Date"
    sort_dir: str = "desc"
    selected_label: Optional[str] = None

    @field_validator("sort_dir", mode="before")
    @classmethod
    def normalize_sort_dir(cls, v):
        if isinstance(v, str):
            val = v.lower().strip()
            return "asc" if val == "asc" else "desc"
        return "desc"


class ExportCsvSchema(BaseFilterSchema):
    """Schema for POST /api/export/csv."""
    pass


class LabelAnalysisSchema(BaseFilterSchema):
    """Schema for POST /api/label-analysis."""
    label: str = ""

    @field_validator("label", mode="before")
    @classmethod
    def clean_label(cls, v):
        if v is None:
            return ""
        return str(v).strip()


class ReloadRequestSchema(BaseModel):
    """Schema for POST /api/reload."""
    model_config = ConfigDict(extra="ignore")
    custom_path: Optional[str] = None

    @field_validator("custom_path", mode="before")
    @classmethod
    def clean_path(cls, v):
        if v is not None and isinstance(v, str) and not v.strip():
            return None
        return v
