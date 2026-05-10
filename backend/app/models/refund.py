from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from app.database import Base


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    review_status = Column(String(20), nullable=False, default="pending")  # pending | approved | rejected
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
