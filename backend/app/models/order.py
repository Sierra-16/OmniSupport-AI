from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    total_amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=True)
    logistics_no = Column(String(100), nullable=True)
    logistics_status = Column(String(500), nullable=True)  # JSON string
    items = Column(String(2000), nullable=False)  # JSON string: [{product_id, quantity, price}]
    created_at = Column(DateTime, server_default=func.now())
