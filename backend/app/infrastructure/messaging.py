import json
import uuid

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message

from app.core.config import settings

TASK_EXCHANGE = "cloudtask.tasks"
RETRY_EXCHANGE = "cloudtask.retry"
DEAD_LETTER_EXCHANGE = "cloudtask.dlx"
TASK_QUEUE = "cloudtask.csv-analysis"
RETRY_QUEUE = "cloudtask.csv-analysis.retry"
DEAD_LETTER_QUEUE = "cloudtask.csv-analysis.dlq"
ROUTING_KEY = "csv_analysis"


async def declare_topology(channel: aio_pika.abc.AbstractChannel) -> aio_pika.abc.AbstractExchange:
    task_exchange = await channel.declare_exchange(TASK_EXCHANGE, ExchangeType.DIRECT, durable=True)
    retry_exchange = await channel.declare_exchange(RETRY_EXCHANGE, ExchangeType.DIRECT, durable=True)
    dead_letter_exchange = await channel.declare_exchange(DEAD_LETTER_EXCHANGE, ExchangeType.DIRECT, durable=True)

    task_queue = await channel.declare_queue(
        TASK_QUEUE,
        durable=True,
        arguments={
            "x-dead-letter-exchange": DEAD_LETTER_EXCHANGE,
            "x-dead-letter-routing-key": ROUTING_KEY,
        },
    )
    await task_queue.bind(task_exchange, routing_key=ROUTING_KEY)

    retry_queue = await channel.declare_queue(
        RETRY_QUEUE,
        durable=True,
        arguments={
            "x-message-ttl": settings.retry_delay_seconds * 1000,
            "x-dead-letter-exchange": TASK_EXCHANGE,
            "x-dead-letter-routing-key": ROUTING_KEY,
        },
    )
    await retry_queue.bind(retry_exchange, routing_key=ROUTING_KEY)

    dead_letter_queue = await channel.declare_queue(DEAD_LETTER_QUEUE, durable=True)
    await dead_letter_queue.bind(dead_letter_exchange, routing_key=ROUTING_KEY)
    return task_exchange


class TaskPublisher:
    def __init__(self) -> None:
        self.connection: aio_pika.abc.AbstractRobustConnection | None = None
        self.channel: aio_pika.abc.AbstractChannel | None = None
        self.task_exchange: aio_pika.abc.AbstractExchange | None = None
        self.retry_exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        self.connection = await aio_pika.connect_robust(settings.required("rabbitmq_url"))
        self.channel = await self.connection.channel(publisher_confirms=True)
        self.task_exchange = await declare_topology(self.channel)
        self.retry_exchange = await self.channel.get_exchange(RETRY_EXCHANGE)

    async def publish(self, task_id: uuid.UUID, attempt: int = 0, retry: bool = False) -> None:
        if self.task_exchange is None or self.retry_exchange is None:
            raise RuntimeError("TaskPublisher must be connected before publishing")
        message = Message(
            json.dumps({"task_id": str(task_id), "attempt": attempt}).encode("utf-8"),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
            message_id=str(uuid.uuid4()),
            correlation_id=str(task_id),
        )
        exchange = self.retry_exchange if retry else self.task_exchange
        await exchange.publish(message, routing_key=ROUTING_KEY, mandatory=True)

    async def close(self) -> None:
        if self.connection is not None:
            await self.connection.close()


async def publish_task(task_id: uuid.UUID) -> None:
    publisher = TaskPublisher()
    try:
        await publisher.connect()
        await publisher.publish(task_id)
    finally:
        await publisher.close()
