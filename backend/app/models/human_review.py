from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.database import Base


class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    checkpoint_id = Column(Integer, nullable=False)  # LangGraph thread_id (conversation_id) for MemorySaver resume
    action_type = Column(String(50), nullable=False)  # refund_approval | takeover | escalation
    status = Column(String(20), nullable=False, default="pending")  # pending | approved | rejected | closed
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
