### payment_service/app/schemas.py
from pydantic import BaseModel
from datetime import datetime

class PaymentCreate(BaseModel):
    order_id: str
    event_id: str
    event_name: str
    quantity: int
    total_price: float
    order_time: datetime