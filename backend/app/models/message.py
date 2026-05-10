from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, func
from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user | assistant | tool | system
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    extra_data = Column(String(1000), nullable=True)  # JSON string
    created_at = Column(DateTime, server_default=func.now())
