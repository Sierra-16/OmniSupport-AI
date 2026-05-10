from sqlalchemy import Column, Integer, String, DateTime, Text, func
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False, default=0)
    source_url = Column(String(500), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
