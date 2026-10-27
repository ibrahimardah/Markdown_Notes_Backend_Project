from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from db.database import Base
from sqlalchemy.sql import func

class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    # Recursive Relationship
    parent_id = Column(Integer, ForeignKey("folders.id"))
    created_at = Column(DateTime, default=func.now(), nullable=False)