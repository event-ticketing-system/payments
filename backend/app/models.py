from sqlalchemy import Column, Integer, String, Float, DateTime
from .database import Base
from datetime import datetime

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, nullable=False)
    event_id = Column(String, nullable=False)
    event_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)  # 👈 Not "amount"
    payment_status = Column(String, default="pending")
    payment_time = Column(DateTime, default=datetime.utcnow)
    merchant_transaction_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)