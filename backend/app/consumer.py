import aio_pika
import asyncio
import json
import time
from app.database import SessionLocal
from app import models
import datetime
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")

async def handle_order_created(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        print("Received order_created:", data)

        db = SessionLocal()
        try:
            existing_payment = db.query(models.Payment).filter_by(merchant_transaction_id=data["merchant_transaction_id"]).first()
            if existing_payment:
                existing_payment.event_id = data["event_id"]
                existing_payment.event_name = data["event_name"]
                existing_payment.quantity = data["quantity"]
                existing_payment.total_price = data["total_price"]
                existing_payment.user_id = data["user_id"]
                existing_payment.payment_status = "pending"
                db.commit()
                print(f"Payment record updated for order {data['order_id']}")
            else:
                new_payment = models.Payment(
                    order_id=data["order_id"],
                    event_id=data["event_id"],
                    event_name=data["event_name"],
                    quantity=data["quantity"],
                    total_price=data["total_price"],
                    payment_status="pending",
                    merchant_transaction_id=data["merchant_transaction_id"],
                    user_id=data["user_id"] 
                )
                db.add(new_payment)
                db.commit()
                print(f"New payment record created for order {data['order_id']}")
        except Exception as e:
            print(f"Payment handling failed: {e}")
            db.rollback()
        finally:
            db.close()

async def consume():
    while True:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            break
        except Exception as e:
            print("Waiting for RabbitMQ to be ready...")
            await asyncio.sleep(5)

    channel = await connection.channel()
    exchange = await channel.declare_exchange("order_events", aio_pika.ExchangeType.TOPIC)
    queue = await channel.declare_queue("payment_queue", durable=True)
    await queue.bind(exchange, routing_key="order_created")
    await queue.consume(handle_order_created)

    print(" [*] Listening for order_created messages.")
