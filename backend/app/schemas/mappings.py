from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class HeaderMappingRead(BaseModel):
    id: str
    batch_id: str
    batch_name: str
    source_file_id: str
    source_file_name: str
    raw_header: str
    raw_header_signature: str
    canonical_field: Optional[str]
    mapping_source: str
    confidence: Optional[float]
    candidate_fields: list[str]
    manually_overridden: bool


class HeaderMappingListRead(BaseModel):
    items: list[HeaderMappingRead]
    available_canonical_fields: list[str]


class HeaderMappingUpdateRequest(BaseModel):
    canonical_field: Optional[str] = Field(default=None)
