import asyncio
import json
import logging
import uuid

import aio_pika
from prometheus_client import start_http_server

from app.core.config import settings
from app.core.errors import CsvAnalysisError, RetryableProcessingError
from app.core.metrics import TASK_DURATION, TASK_OUTCOMES
from app.infrastructure.messaging import RETRY_EXCHANGE, TASK_QUEUE, declare_topology, publish_task
from app.worker.service import (
    mark_failed,
    mark_outbox_failed,
    mark_outbox_published,
    mark_pending_for_retry,
    process_task,
    recover_expired_processing_tasks,
    unpublished_outbox_task_ids,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def _decode_task_message(message: aio_pika.IncomingMessage) -> tuple[uuid.UUID, int]:
    payload = json.loads(message.body.decode("utf-8"))
    return uuid.UUID(payload["task_id"]), int(payload.get("attempt", 0))


async def consume() -> None:
    connection = await aio_pika.connect_robust(settings.required("rabbitmq_url"))
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        await declare_topology(channel)
        retry_exchange = await channel.get_exchange(RETRY_EXCHANGE)
        queue = await channel.get_queue(TASK_QUEUE)

        async def handle(message: aio_pika.IncomingMessage) -> None:
            try:
                task_id, attempt = _decode_task_message(message)
            except (ValueError, KeyError, json.JSONDecodeError):
                logger.warning("Discarding malformed task message")
                await message.reject(requeue=False)
                return

            try:
                with TASK_DURATION.time():
                    processed = await asyncio.to_thread(process_task, task_id)
                TASK_OUTCOMES.labels("completed" if processed else "duplicate").inc()
                await message.ack()
            except CsvAnalysisError as error:
                await asyncio.to_thread(mark_failed, task_id, str(error))
                TASK_OUTCOMES.labels("failed").inc()
                await message.reject(requeue=False)
            except RetryableProcessingError:
                if attempt + 1 >= settings.max_attempts:
                    await asyncio.to_thread(mark_failed, task_id, "Processing could not be completed after several attempts.")
                    TASK_OUTCOMES.labels("failed").inc()
                    await message.reject(requeue=False)
                    return
                await asyncio.to_thread(mark_pending_for_retry, task_id)
                retry_message = aio_pika.Message(
                    json.dumps({"task_id": str(task_id), "attempt": attempt + 1}).encode("utf-8"),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    content_type="application/json",
                    correlation_id=str(task_id),
                )
                try:
                    await retry_exchange.publish(retry_message, routing_key="csv_analysis", mandatory=True)
                    TASK_OUTCOMES.labels("retry").inc()
                    await message.ack()
                except Exception:
                    logger.exception("Could not schedule retry for task %s", task_id)
                    await message.nack(requeue=True)

        await queue.consume(handle)
        asyncio.create_task(reconcile_outbox())
        start_http_server(settings.metrics_port)
        logger.info("CloudTask worker is consuming queue %s", TASK_QUEUE)
        await asyncio.Future()


async def reconcile_outbox() -> None:
    """Publish committed tasks after transient broker failures and recover abandoned leases."""
    while True:
        try:
            recovered = await asyncio.to_thread(recover_expired_processing_tasks, settings.task_lease_seconds)
            if recovered:
                logger.warning("Recovered %s expired processing lease(s)", recovered)
            task_ids = await asyncio.to_thread(unpublished_outbox_task_ids)
            for task_id in task_ids:
                try:
                    await publish_task(task_id)
                    await asyncio.to_thread(mark_outbox_published, task_id)
                except Exception:
                    logger.exception("Could not publish outbox task %s", task_id)
                    await asyncio.to_thread(mark_outbox_failed, task_id)
        except Exception:
            logger.exception("Outbox reconciliation cycle failed")
        await asyncio.sleep(settings.outbox_poll_seconds)


def main() -> None:
    asyncio.run(consume())


if __name__ == "__main__":
    main()
