import pytest
import asyncio
from packages.shared_contracts.events import (
    EventEnvelope, QCEventType, InspectionCreatedPayload, QualityVerdict
)
from packages.shared_contracts.events import (
    BusinessEventEnvelope, BusinessEventType, DraftOrderPayload
)
from apps.enterprise_copilot.backend.rabbitmq import RabbitMQBroker


def test_qc_8_events_serialization():
    envelope = EventEnvelope(
        event_type=QCEventType.INSPECTION_CREATED,
        correlation_id="corr-1234",
        partition_key="INSP-001",
        payload=InspectionCreatedPayload(
            inspection_id="INSP-001",
            work_order_id="WO-1",
            batch_number="B-1",
            item_code="ALU-01",
            facility_id="FAC-01",
            operator_id="OP-01",
        ).model_dump(),
    )
    dumped = envelope.model_dump()
    assert dumped["event_type"] == "inspection.created"
    assert dumped["schema_version"] == "1.0"
    assert dumped["correlation_id"] == "corr-1234"
    assert len(dumped["idempotency_key"]) == 64  # SHA-256


def test_rabbitmq_outbox_dlq_routing():
    broker = RabbitMQBroker()
    broker.enabled = False  # Test in-memory queue & DLQ logic

    event = BusinessEventEnvelope(
        event_type=BusinessEventType.DRAFT_ORDER_CREATED,
        correlation_id="corr-999",
        tenant_id="TENANT-001",
        maker_id="maker-1",
        payload={"order_id": "ORD-1"},
    )

    asyncio.run(broker.publish_event(event))
    assert len(broker._memory_queue) == 1

    # Handler that fails intentionally to test retry & DLQ
    def failing_handler(item):
        raise ValueError("Simulated ERP connection timeout")

    # Run outbox processor with max_retries = 2
    for _ in range(3):
        asyncio.run(broker.process_outbox_queue(failing_handler, max_retries=2))

    # Should now be moved to Dead Letter Queue (DLQ)
    assert len(broker._dlq_queue) == 1
    assert "Simulated ERP connection timeout" in broker._dlq_queue[0]["dlq_reason"]
