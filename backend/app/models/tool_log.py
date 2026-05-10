from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, func
from app.database import Base


class ToolLog(Base):
    __tablename__ = "tool_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    tool_name = Column(String(100), nullable=False)
    input_params = Column(Text, nullable=True)  # JSON string
    output = Column(Text, nullable=True)  # JSON string
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
