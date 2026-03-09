from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PageInfo(BaseModel):
    number: int
    width: float
    height: float
    rotation: int = 0


class DocumentResponse(BaseModel):
    id: UUID
    original_filename: str
    file_size: int
    page_count: int | None = None
    pages: list[PageInfo] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int = 0


class UploadResponse(BaseModel):
    id: UUID
    job_id: UUID
    original_filename: str


class UploadBatchResponse(BaseModel):
    uploads: list[UploadResponse]


class DetectedTable(BaseModel):
    page: int
    x1: float
    y1: float
    x2: float
    y2: float
    width: float
    height: float


class DetectedTablesResponse(BaseModel):
    tables: list[DetectedTable]
