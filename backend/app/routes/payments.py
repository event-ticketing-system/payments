from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app import models, rabbitmq
from app.database import SessionLocal
import logging
import base64
import hashlib
import json
import httpx
import datetime

router = APIRouter()

# Payment provider config (replace with your actual secure values)
MERCHANT_ID = "PGTESTPAYUAT86"
SALT_KEY = "96434309-7796-489d-8924-ab56988a6076"
SALT_INDEX = 1
PHONE_PE_HOST_URL = "https://api-preprod.phonepe.com/apis/pg-sandbox"
FRONTEND_URL = "http://localhost:3002"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/pay")
async def initiate_payment(
    amount: float = Query(...),
    user_id: str = Query(...),
    order_id: int = Query(...),
    merchant_transaction_id: str = Query(...),
    db: Session = Depends(get_db)
):
    logging.info(f"Initiating payment of ₹{amount} for order {order_id} by user {user_id}")

    try:
        # Wait for the consumer to process the order_created event and create the payment record
        db_payment = None
        for _ in range(5):  # Retry up to 5 times with 1s delay
            db_payment = db.query(models.Payment).filter_by(merchant_transaction_id=merchant_transaction_id).first()
            if db_payment:
                break
            await asyncio.sleep(1)

        if not db_payment:
            raise HTTPException(status_code=404, detail="Payment record not found")

        # Prepare PhonePe payment payload
        payload = {
            "merchantId": MERCHANT_ID,
            "merchantTransactionId": merchant_transaction_id,
            "merchantUserId": user_id,
            "amount": int(amount * 100),  # Convert to paise
            "redirectUrl": f"http://localhost:8001/api/payments/payment/validate/{merchant_transaction_id}",
            "redirectMode": "REDIRECT",
            "mobileNumber": "9999999999",  # Placeholder
            "paymentInstrument": {
                "type": "PAY_PAGE"
            }
        }

        json_payload = json.dumps(payload).encode("utf-8")
        base64_encoded_payload = base64.b64encode(json_payload).decode("utf-8")
        checksum_str = base64_encoded_payload + "/pg/v1/pay" + SALT_KEY
        sha256_hash = hashlib.sha256(checksum_str.encode("utf-8")).hexdigest()
        x_verify = f"{sha256_hash}###{SALT_INDEX}"

        # Send request to PhonePe
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PHONE_PE_HOST_URL}/pg/v1/pay",
                json={"request": base64_encoded_payload},
                headers={
                    "Content-Type": "application/json",
                    "X-VERIFY": x_verify,
                    "accept": "application/json"
                }
            )

        data = response.json()
        logging.info(f"PhonePe /pay response: {data}")

        # Redirect user to PhonePe payment page
        if data.get("success") and data.get("code") == "PAYMENT_INITIATED":
            redirect_url = data["data"]["instrumentResponse"]["redirectInfo"]["url"]
            return {"payment_url": redirect_url}

        # On failure
        return {"error": "initiation_failed"}

    except Exception as e:
        logging.error(f"Error in initiate_payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/payment/validate/{merchant_transaction_id}")
async def validate_payment(merchant_transaction_id: str, db: Session = Depends(get_db)):
    try:
        status_path = f"/pg/v1/status/{MERCHANT_ID}/{merchant_transaction_id}"
        status_url = PHONE_PE_HOST_URL + status_path

        # Create checksum for status call
        string = status_path + SALT_KEY
        sha256_hash = hashlib.sha256(string.encode('utf-8')).hexdigest()
        x_verify = f"{sha256_hash}###{SALT_INDEX}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                status_url,
                headers={
                    "Content-Type": "application/json",
                    "X-VERIFY": x_verify,
                    "accept": "application/json"
                }
            )

        logging.info(f"PhonePe status response: {response.status_code} {response.text}")

        try:
            data = response.json()
        except Exception as json_err:
            logging.error(f"Failed to parse JSON response: {json_err}")
            raise HTTPException(status_code=500, detail="Payment API returned invalid response")

        if data.get("success") and data.get("code") == "PAYMENT_SUCCESS":
            payment = db.query(models.Payment).filter_by(merchant_transaction_id=merchant_transaction_id).first()

            if payment:
                payment.payment_status = "complete"
                db.commit()

                # Send message to RabbitMQ or whatever your pub-sub setup is
                await rabbitmq.publish_event("payment_completed", {
                    "transaction_id": merchant_transaction_id,
                    "order_id": payment.order_id,
                    "status": "complete",
                    "time": datetime.datetime.utcnow().isoformat()
                })

                return RedirectResponse(f"{FRONTEND_URL}/payment/status?status=success")

        return RedirectResponse(f"{FRONTEND_URL}/payment/status?status=error")

    except Exception as e:
        logging.error(f"Error validating payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Error validating payment")