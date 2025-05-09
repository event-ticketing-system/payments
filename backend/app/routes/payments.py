import datetime
from fastapi import APIRouter, Depends, HTTPException
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

@router.post("/")
async def process_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db)):
    db_payment = models.Payment(
        order_id=payment.order_id,
        event_id=payment.event_id,
        event_name=payment.event_name,
        quantity=payment.quantity,
        total_price=payment.total_price,
        payment_status="pending"
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

@router.get("/pending")
def get_pending_payments(db: Session = Depends(get_db)):
    payments = db.query(models.Payment).filter(models.Payment.payment_status == "pending").all()
    return payments


@router.post("/confirm/{order_id}")
async def confirm_payment(order_id: str, db: Session = Depends(get_db)):
    print(f"Confirming payment for order_id: {order_id}")
    payment = db.query(models.Payment).filter(models.Payment.order_id == order_id).first()
    if not payment:
        print("Payment not found")
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.payment_status != "pending":
        print(f"Payment already processed: {payment.payment_status}")
        raise HTTPException(status_code=400, detail="Payment is not pending")

    try:
        payment.payment_status = "paid"
        payment.payment_time = datetime.datetime.utcnow()
        db.commit()
        db.refresh(payment)

        print(f"Payment confirmed: {payment.id}")
        await rabbitmq.publish_event("payment_completed", {
            "order_id": payment.order_id,
            "event_id": payment.event_id,
            "total_price": payment.total_price,
            "payment_time": payment.payment_time.isoformat()
        })

        return {"message": "Payment confirmed", "payment_id": payment.id}

    except Exception as e:
        print(f"Error during confirmation: {e}")
        raise HTTPException(status_code=500, detail=str(e))