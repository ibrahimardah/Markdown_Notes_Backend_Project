from datetime import datetime
from pydantic import BaseModel

class FolderCreate(BaseModel):
    name: str
    parent_id: int | None = None

class FolderUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None

class FolderResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    parent_id: int | None
    created_at: datetime
    model_config = {"from_attributes": True}