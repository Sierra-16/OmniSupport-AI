from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    channel = Column(String(20), nullable=False, default="web")
    summary = Column(String(1000), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
