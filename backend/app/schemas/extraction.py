from pydantic import BaseModel


class ExtractionSelection(BaseModel):
    page: int
    x1: float
    y1: float
    x2: float
    y2: float
    extraction_method: str = "guess"


class ExtractionRequest(BaseModel):
    selections: list[ExtractionSelection]


class TableResult(BaseModel):
    spec_index: int
    page: int
    data: list[list[str]]


class ExtractionResponse(BaseModel):
    tables: list[TableResult]
