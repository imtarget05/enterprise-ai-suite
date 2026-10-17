"""
Shared Database Models for Monorepo (PostgreSQL 16).
Provides persistent relational schemas for Users, Orders, Outbox Messages,
Inspections, Defects, and Audit Trails.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    roles = Column(JSON, nullable=False)
    tenant_id = Column(String(64), nullable=False, index=True)
    facility_id = Column(String(64), nullable=False)
    department = Column(String(64), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(64), nullable=False, index=True)
    customer_name = Column(String(128), nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(8), default="USD")
    status = Column(String(32), default="DRAFT", index=True)
    maker_id = Column(String(36), nullable=False)
    checker_id = Column(String(36), nullable=True)
    erp_reference_id = Column(String(64), nullable=True, index=True)
    salesforce_id = Column(String(64), nullable=True, index=True)
    items_data = Column(JSON, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OutboxMessageModel(Base):
    __tablename__ = "outbox_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(64), nullable=False, index=True)
    destination = Column(String(32), nullable=False)  # "rabbitmq" or "redpanda"
    topic_or_exchange = Column(String(64), nullable=False)
    routing_key = Column(String(64), nullable=False)
    correlation_id = Column(String(64), nullable=False, index=True)
    idempotency_key = Column(String(64), unique=True, nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    status = Column(String(32), default="PENDING", index=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class InspectionModel(Base):
    __tablename__ = "inspections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(64), nullable=False, index=True)
    facility_id = Column(String(64), nullable=False)
    batch_number = Column(String(64), nullable=False, index=True)
    work_order_id = Column(String(64), nullable=False)
    item_code = Column(String(64), nullable=False, index=True)
    operator_id = Column(String(36), nullable=False)
    reviewer_id = Column(String(36), nullable=True)
    image_uri = Column(String(256), nullable=False)
    image_sha256 = Column(String(64), nullable=False)
    inference_latency_ms = Column(Float, default=0.0)
    verdict = Column(String(32), default="PENDING_REVIEW", index=True)
    erp_qc_id = Column(String(64), nullable=True, index=True)
    rule_reasons = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    defects = relationship("DefectModel", back_populates="inspection", cascade="all, delete-orphan")


class DefectModel(Base):
    __tablename__ = "defects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("inspections.id"), nullable=False)
    class_id = Column(Integer, nullable=False)
    class_name = Column(String(64), nullable=False)
    confidence = Column(Float, nullable=False)
    severity = Column(String(32), nullable=False)
    x_min = Column(Float, nullable=False)
    y_min = Column(Float, nullable=False)
    x_max = Column(Float, nullable=False)
    y_max = Column(Float, nullable=False)
    area_ratio = Column(Float, default=0.0)

    inspection = relationship("InspectionModel", back_populates="defects")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(36), nullable=False)
    action = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    details = Column(JSON, nullable=True)
    sha256_stamp = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
