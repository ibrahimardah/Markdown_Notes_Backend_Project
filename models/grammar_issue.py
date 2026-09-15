from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from db.database import Base

class GrammarIssue(Base):
    __tablename__ = "grammar_issues"

    id = Column(Integer, primary_key=True)
    revision_id = Column(Integer, ForeignKey("revisions.id"), nullable=False)
    offset = Column(Integer, nullable=False)
    length = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    rule_id = Column(String)
    suggestions = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)