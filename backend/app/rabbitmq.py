import aio_pika
import json
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")

async def publish_event(routing_key: str, payload: dict):
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("order_events", aio_pika.ExchangeType.TOPIC)
        await exchange.publish(
            aio_pika.Message(body=json.dumps(payload).encode()),
            routing_key=routing_key,
        )
