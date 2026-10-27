from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from db.database import Base

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    # unique name per owner constraint
    __table_args__ = (UniqueConstraint("owner_id", "name"),)