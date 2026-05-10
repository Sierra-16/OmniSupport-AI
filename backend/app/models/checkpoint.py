from sqlalchemy import Column, Integer, String, DateTime, Text, func
from app.database import Base


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(255), nullable=False, index=True)
    checkpoint_ns = Column(String(255), nullable=False, default="")
    checkpoint = Column(Text, nullable=False)
    extra_data = Column(String(1000), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
