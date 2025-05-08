from sqlalchemy import Column, Integer, String, Float, DateTime
from .database import Base
import datetime

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, index=True)
    event_id = Column(String)
    event_name = Column(String)
    quantity = Column(Integer)
    total_price = Column(Float)
    payment_status = Column(String, default="pending")
    payment_time = Column(DateTime, default=datetime.datetime.utcnow)