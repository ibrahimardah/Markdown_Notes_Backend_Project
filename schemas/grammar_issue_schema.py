from datetime import datetime
from pydantic import BaseModel

class GrammarIssueResponse(BaseModel):
    id: int
    revision_id: int
    offset: int
    length: int
    message: str
    rule_id: str | None
    suggestions: list[str]
    created_at: datetime
    model_config = {"from_attributes": True}