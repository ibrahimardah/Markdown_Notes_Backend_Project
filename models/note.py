from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from db.database import Base
from sqlalchemy.sql import func

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    body_markdown = Column(Text, nullable=False)
    folder_id = Column(Integer, ForeignKey("folders.id"))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)