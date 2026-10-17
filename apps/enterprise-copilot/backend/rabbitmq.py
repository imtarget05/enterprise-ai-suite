"""
RabbitMQ Asynchronous Processing Engine & Transactional Outbox for Project 1.
"""

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional
from apps.enterprise_copilot.backend.config import settings
from packages.shared_contracts.events import BusinessEventEnvelope


class RabbitMQBroker:
    def __init__(self):
        self.url = settings.RABBITMQ_URL
        self.exchange_name = settings.RABBITMQ_EXCHANGE
        self.enabled = settings.RABBITMQ_ENABLED
        self._connection = None
        self._channel = None
        self._memory_queue: List[Dict[str, Any]] = []
        self._dlq_queue: List[Dict[str, Any]] = []
        self._processed_idempotency_keys: set = set()

    async def connect(self) -> None:
        if not self.enabled:
            return
        try:
            import aio_pika
            self._connection = await aio_pika.connect_robust(self.url)
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=10)
        except Exception:
            self.enabled = False

    async def publish_event(self, event: BusinessEventEnvelope, routing_key: str = "business.orders") -> bool:
        if event.idempotency_key in self._processed_idempotency_keys:
            return True

        if self.enabled and self._channel:
            try:
                import aio_pika
                exchange = await self._channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)
                message = aio_pika.Message(
                    body=json.dumps(event.model_dump()).encode("utf-8"),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    correlation_id=event.correlation_id,
                    message_id=event.event_id,
                )
                await exchange.publish(message, routing_key=routing_key)
                self._processed_idempotency_keys.add(event.idempotency_key)
                return True
            except Exception:
                pass

        self._memory_queue.append({"event": event.model_dump(), "routing_key": routing_key, "retry_count": 0})
        self._processed_idempotency_keys.add(event.idempotency_key)
        return True

    async def process_outbox_queue(self, handler: Callable[[Dict[str, Any]], bool], max_retries: int = 3) -> int:
        processed = 0
        remaining_queue = []

        while self._memory_queue:
            item = self._memory_queue.pop(0)
            try:
                if handler(item["event"]):
                    processed += 1
                else:
                    raise RuntimeError("Handler returned failure")
            except Exception as e:
                item["retry_count"] += 1
                if item["retry_count"] > max_retries:
                    item["dlq_reason"] = str(e)
                    self._dlq_queue.append(item)
                else:
                    remaining_queue.append(item)

        self._memory_queue = remaining_queue
        return processed


rabbitmq_broker = RabbitMQBroker()
