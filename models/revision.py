from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from db.database import Base
from sqlalchemy.sql import func

class Revision(Base):
    __tablename__ = "revisions"

    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    revision_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    body_markdown = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)