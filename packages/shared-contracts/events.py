"""
Shared Contract Events for Monorepo (Enterprise Copilot & Visual Quality Gate).
Strictly versioned Pydantic schemas for the 8 QC lifecycle events and RabbitMQ business events.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
import hashlib
from pydantic import BaseModel, Field


# -------------------------------------------------------------
# QC Lifecycle Events (Project 2: Visual Quality Gate)
# -------------------------------------------------------------

class QCEventType(str, Enum):
    INSPECTION_CREATED = "inspection.created"
    IMAGE_UPLOADED = "inspection.image.uploaded"
    INFERENCE_COMPLETED = "inspection.inference.completed"
    REVIEW_COMPLETED = "inspection.review.completed"
    QUALITY_DECIDED = "inspection.quality.decided"
    ERP_SYNC_REQUESTED = "inspection.erp.sync.requested"
    ERP_SYNC_COMPLETED = "inspection.erp.sync.completed"
    ERP_SYNC_FAILED = "inspection.erp.sync.failed"


class DefectSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    NEGLIGIBLE = "NEGLIGIBLE"


class QualityVerdict(str, Enum):
    PASSED = "PASSED"
    QUARANTINE = "QUARANTINE"
    REJECTED = "REJECTED"
    PENDING_REVIEW = "PENDING_REVIEW"


class BoundingBox(BaseModel):
    x_min: float = Field(..., ge=0.0, le=1.0)
    y_min: float = Field(..., ge=0.0, le=1.0)
    x_max: float = Field(..., ge=0.0, le=1.0)
    y_max: float = Field(..., ge=0.0, le=1.0)
    class_id: int
    class_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: DefectSeverity = DefectSeverity.MINOR
    area_ratio: float = Field(default=0.0, ge=0.0, le=1.0)


class InspectionCreatedPayload(BaseModel):
    inspection_id: str
    work_order_id: str
    batch_number: str
    item_code: str
    facility_id: str
    operator_id: str


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: QCEventType
    schema_version: str = "1.0"
    correlation_id: str
    partition_key: str  # inspection_id
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    retry_count: int = 0
    idempotency_key: str = ""
    payload: Dict[str, Any]

    def model_post_init(self, __context: Any) -> None:
        if not self.idempotency_key:
            raw = f"{self.event_type}:{self.correlation_id}:{self.partition_key}"
            self.idempotency_key = hashlib.sha256(raw.encode("utf-8")).hexdigest()


# -------------------------------------------------------------
# Business Events (Project 1: Enterprise Copilot)
# -------------------------------------------------------------

class BusinessEventType(str, Enum):
    DRAFT_ORDER_CREATED = "business.order.draft_created"
    APPROVAL_REQUESTED = "business.order.approval_requested"
    ORDER_APPROVED = "business.order.approved"
    ORDER_REJECTED = "business.order.rejected"
    ERP_SYNC_DISPATCHED = "business.erp.sync_dispatched"
    ERP_SYNC_ACKNOWLEDGED = "business.erp.sync_acknowledged"


class DraftOrderPayload(BaseModel):
    order_id: str
    customer_id: Optional[str] = None
    total_amount: Optional[float] = 0.0
    currency: str = "USD"
    items: Optional[List[Dict[str, Any]]] = None


class BusinessEventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: BusinessEventType
    correlation_id: str
    tenant_id: str
    maker_id: str
    checker_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    idempotency_key: str = ""
    payload: Dict[str, Any]

    def model_post_init(self, __context: Any) -> None:
        if not self.idempotency_key:
            raw = f"{self.event_type}:{self.correlation_id}:{self.tenant_id}"
            self.idempotency_key = hashlib.sha256(raw.encode("utf-8")).hexdigest()
