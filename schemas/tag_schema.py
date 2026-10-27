from pydantic import BaseModel

class TagCreate(BaseModel):
    name: str

class TagUpdate(BaseModel):
    name: str

class TagResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    model_config = {"from_attributes": True}