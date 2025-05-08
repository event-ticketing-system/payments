from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas, models, rabbitmq
from app.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/api/payments")
async def process_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db)):
    db_payment = models.Payment(
        order_id=payment.order_id,
        event_id=payment.event_id,
        event_name=payment.event_name,
        quantity=payment.quantity,
        total_price=payment.total_price,
        payment_status="confirmed"
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)

    # Notify via RabbitMQ
    await rabbitmq.publish_event("payment_successful", {
        "order_id": payment.order_id,
        "event_name": payment.event_name,
        "total_price": payment.total_price,
        "payment_time": db_payment.payment_time.isoformat()
    })

    return {"message": "Payment processed", "payment_id": db_payment.id}