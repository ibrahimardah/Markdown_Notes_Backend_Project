from datetime import datetime
from pydantic import BaseModel, Field

class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body_markdown: str
    folder_id: int | None = None

class NoteResponse(BaseModel):
    id: int
    owner_id: int
    title: str
    body_markdown: str
    folder_id: int | None
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None
    model_config = {"from_attributes": True}

class NoteFilterParams(BaseModel):
    folder_id: int | None = None
    tag: str | None = None
    q: str | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body_markdown: str | None = None
    folder_id: int | None = None