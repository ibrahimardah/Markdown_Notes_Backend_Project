from datetime import datetime
from pydantic import BaseModel

class RevisionResponse(BaseModel):
    id: int
    note_id: int
    revision_number: int
    title: str
    body_markdown: str
    created_at: datetime
    created_by: int
    model_config = {"from_attributes": True}