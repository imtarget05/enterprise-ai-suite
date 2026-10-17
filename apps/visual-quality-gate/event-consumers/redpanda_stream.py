"""
Redpanda / Kafka Streaming Client for Product B.
Manages all 8 required QC lifecycle events:
- inspection.created
- inspection.image.uploaded
- inspection.inference.completed
- inspection.review.completed
- inspection.quality.decided
- inspection.erp.sync.requested
- inspection.erp.sync.completed
- inspection.erp.sync.failed
"""

import json
from typing import Any, Callable, Dict, List, Optional
from apps.visual_quality_gate.backend.config import qc_settings
from packages.shared_contracts.events import EventEnvelope, QCEventType


class RedpandaQCStream:
    def __init__(self):
        self.bootstrap_servers = qc_settings.KAFKA_BOOTSTRAP_SERVERS
        self.topic = qc_settings.KAFKA_TOPIC_QC
        self.enabled = qc_settings.KAFKA_ENABLED
        self._producer = None
        self._memory_log: List[Dict[str, Any]] = []
        self._subscribers: Dict[QCEventType, List[Callable[[EventEnvelope], None]]] = {}

        if self.enabled:
            try:
                from kafka import KafkaProducer
                self._producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    key_serializer=lambda k: k.encode("utf-8"),
                )
            except Exception as e:
                print(f"[RedpandaQCStream] Live Kafka/Redpanda connection deferred ({e}). Operating with local event bus.")
                self.enabled = False

    def emit_event(self, event: EventEnvelope) -> None:
        """
        Emits an event to Redpanda topic partitioned by partition_key (inspection_id).
        """
        data = event.model_dump()
        if self.enabled and self._producer:
            try:
                self._producer.send(
                    self.topic,
                    key=event.partition_key,
                    value=data,
                )
                self._producer.flush()
            except Exception as e:
                print(f"[RedpandaQCStream] Kafka publish error: {e}. Storing to memory log.")

        # Local event log persistence
        self._memory_log.append(data)

        # Notify local consumers/subscribers
        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as ex:
                    print(f"[RedpandaQCStream] Subscriber error for {event.event_type}: {ex}")

    def subscribe(self, event_type: QCEventType, callback: Callable[[EventEnvelope], None]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def get_events_for_inspection(self, inspection_id: str) -> List[Dict[str, Any]]:
        return [e for e in self._memory_log if e.get("partition_key") == inspection_id]


qc_stream = RedpandaQCStream()
