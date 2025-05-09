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
            payment = models.Payment(
                order_id=data["order_id"],
                event_id=data["event_id"],
                event_name=data["event_name"],
                quantity=data["quantity"],
                total_price=data["total_price"],
                payment_status="pending",
                payment_time=datetime.datetime.utcnow()
            )
            db.add(payment)
            db.commit()
        except Exception as e:
            print("Payment failed:", e)
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

    print(" [*] Waiting for order_created messages.")
