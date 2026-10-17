"""
Configuration for Product B (Visual QC & Defect Inspection).
"""

import os
from enum import Enum
from typing import Optional
from pydantic_settings import BaseSettings


class ExecutionProfile(str, Enum):
    LOCAL = "local"
    DEMO = "demo"
    FULL = "full"


class QCSettings(BaseSettings):
    PROJECT_NAME: str = "Enterprise Visual QC API"
    VERSION: str = "1.0.0"
    PROFILE: ExecutionProfile = ExecutionProfile.LOCAL
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./enterprise_qc.db")

    # Storage (R2 / MinIO / Local)
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "local")  # "r2", "minio", "local"
    STORAGE_ENDPOINT: Optional[str] = os.getenv("STORAGE_ENDPOINT", None)
    STORAGE_ACCESS_KEY: Optional[str] = os.getenv("STORAGE_ACCESS_KEY", None)
    STORAGE_SECRET_KEY: Optional[str] = os.getenv("STORAGE_SECRET_KEY", None)
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "enterprise-qc-evidence")

    # Kafka / Redpanda Event Bus
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC_QC: str = "enterprise.qc.inspections"
    KAFKA_ENABLED: bool = os.getenv("KAFKA_ENABLED", "false").lower() == "true"

    # ONNX Model & Inference
    ONNX_MODEL_PATH: str = os.getenv("ONNX_MODEL_PATH", "models/defect_yolov8n_quantized.onnx")
    INFERENCE_THREADS: int = int(os.getenv("INFERENCE_THREADS", "2"))
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))
    IOU_THRESHOLD: float = float(os.getenv("IOU_THRESHOLD", "0.50"))

    # ERPNext
    ERPNEXT_URL: str = os.getenv("ERPNEXT_URL", "http://localhost:8080")
    ERPNEXT_API_KEY: str = os.getenv("ERPNEXT_API_KEY", "demo_erp_api_key")
    ERPNEXT_API_SECRET: str = os.getenv("ERPNEXT_API_SECRET", "demo_erp_api_secret")
    ERPNEXT_USE_SANDBOX: bool = os.getenv("ERPNEXT_USE_SANDBOX", "true").lower() == "true"

    class Config:
        env_file = ".env"
        extra = "allow"


qc_settings = QCSettings()
