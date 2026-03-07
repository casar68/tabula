from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SelectionSpec(BaseModel):
    page: int
    x1: float
    y1: float
    x2: float
    y2: float
    width: float
    height: float
    extraction_method: str = "guess"


class TemplateCreate(BaseModel):
    name: str
    selections: list[SelectionSpec]
    page_count: int


class TemplateUpdate(BaseModel):
    name: str | None = None


class TemplateResponse(BaseModel):
    id: UUID
    name: str
    selections: list[SelectionSpec]
    selection_count: int
    page_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TemplateListResponse(BaseModel):
    templates: list[TemplateResponse]
