"""
FastAPI Routes for Project 2 (Visual Quality Gate).
Implements Image Ingestion, ONNX CPU Detection, Deterministic Safety Gate,
Redpanda 8-Event Streaming, Human Review, and Shared ERPNext Quality Sync.
"""

from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from packages.auth_integration.security import (
    UserContext, UserRole, enforce_tenant_isolation, get_current_user, require_roles
)
from packages.shared_contracts.events import (
    BoundingBox, DefectSeverity, EventEnvelope, QCEventType,
    QualityVerdict
)
from packages.shared_contracts.storage_manager import StorageManager
from packages.erpnext_adapter.client import erpnext_adapter
from apps.visual_quality_gate.backend.config import qc_settings
from apps.visual_quality_gate.inference.model_registry import model_registry
from apps.visual_quality_gate.inference.onnx_infer import onnx_detector
from apps.visual_quality_gate.backend.safety_gate import safety_gate
from apps.visual_quality_gate.event_consumers.redpanda_stream import qc_stream

router = APIRouter(prefix="/v1", tags=["Quality Control"])
storage = StorageManager(
    provider=qc_settings.STORAGE_PROVIDER,
    endpoint_url=qc_settings.STORAGE_ENDPOINT,
    access_key=qc_settings.STORAGE_ACCESS_KEY,
    secret_key=qc_settings.STORAGE_SECRET_KEY,
    bucket_name=qc_settings.STORAGE_BUCKET,
)


class ReviewRequest(BaseModel):
    action: str
    override_verdict: Optional[QualityVerdict] = None
    notes: Optional[str] = None


@router.post("/inspections")
async def create_inspection(
    file: UploadFile = File(...),
    item_code: str = Form("ALU-CNC-001"),
    batch_number: str = Form("BATCH-2026-X1"),
    work_order_id: str = Form("WO-9901"),
    user: UserContext = Depends(get_current_user),
):
    inspection_id = f"INSP-{uuid.uuid4().hex[:8].upper()}"
    correlation_id = str(uuid.uuid4())
    image_bytes = await file.read()

    obj_name = f"inspections/{inspection_id}/{file.filename}"
    uri, sha256 = storage.upload_bytes(image_bytes, obj_name, content_type=file.content_type or "image/jpeg")

    # Event 1: inspection.created
    qc_stream.emit_event(
        EventEnvelope(
            event_type=QCEventType.INSPECTION_CREATED,
            correlation_id=correlation_id,
            partition_key=inspection_id,
            payload={
                "inspection_id": inspection_id,
                "work_order_id": work_order_id,
                "batch_number": batch_number,
                "item_code": item_code,
                "facility_id": user.facility_id,
                "operator_id": user.user_id,
            },
        )
    )

    # Event 2: inspection.image.uploaded
    qc_stream.emit_event(
        EventEnvelope(
            event_type=QCEventType.IMAGE_UPLOADED,
            correlation_id=correlation_id,
            partition_key=inspection_id,
            payload={
                "inspection_id": inspection_id,
                "image_id": str(uuid.uuid4()),
                "storage_provider": qc_settings.STORAGE_PROVIDER,
                "storage_uri": uri,
                "sha256_hash": sha256,
                "dimensions": {"width": 1920, "height": 1080},
            },
        )
    )

    # Event 3: Run ONNX CPU Inference
    boxes, latency_ms = onnx_detector.infer_image(image_bytes)
    qc_stream.emit_event(
        EventEnvelope(
            event_type=QCEventType.INFERENCE_COMPLETED,
            correlation_id=correlation_id,
            partition_key=inspection_id,
            payload={
                "inspection_id": inspection_id,
                "model_version": model_registry.get_active_model()["model_id"],
                "inference_engine": "onnxruntime-cpu",
                "latency_ms": latency_ms,
                "defects_found": len(boxes),
                "bounding_boxes": [b.model_dump() for b in boxes],
            },
        )
    )

    # Event 5: Deterministic Safety Gate Decision
    decision = safety_gate.decide_quality(boxes)
    verdict = QualityVerdict(decision["verdict"])
    qc_stream.emit_event(
        EventEnvelope(
            event_type=QCEventType.QUALITY_DECIDED,
            correlation_id=correlation_id,
            partition_key=inspection_id,
            payload={
                "inspection_id": inspection_id,
                "verdict": verdict.value,
                "rejection_reasons": decision["reasons"],
                "rule_evaluations": decision["rule_evaluations"],
            },
        )
    )

    return {
        "inspection_id": inspection_id,
        "correlation_id": correlation_id,
        "image_uri": uri,
        "sha256": sha256,
        "latency_ms": latency_ms,
        "defects": [b.model_dump() for b in boxes],
        "verdict": verdict.value,
        "reasons": decision["reasons"],
        "rule_evaluations": decision["rule_evaluations"],
    }


@router.post("/inspections/{inspection_id}/review")
async def review_inspection(
    inspection_id: str,
    req: ReviewRequest,
    user: UserContext = Depends(require_roles([UserRole.QC_INSPECTOR, UserRole.CHECKER, UserRole.SYSTEM_ADMIN])),
):
    qc_stream.emit_event(
        EventEnvelope(
            event_type=QCEventType.REVIEW_COMPLETED,
            correlation_id=str(uuid.uuid4()),
            partition_key=inspection_id,
            payload={
                "inspection_id": inspection_id,
                "reviewer_id": user.user_id,
                "action": req.action,
                "review_notes": req.notes,
            },
        )
    )
    return {"status": "REVIEW_RECORDED", "inspection_id": inspection_id}


@router.post("/inspections/{inspection_id}/sync-erp")
async def sync_inspection_to_erp(
    inspection_id: str,
    item_code: str = "ALU-CNC-001",
    batch_number: str = "BATCH-2026-X1",
    verdict: QualityVerdict = QualityVerdict.PASSED,
    user: UserContext = Depends(require_roles([UserRole.QC_INSPECTOR, UserRole.CHECKER, UserRole.SYSTEM_ADMIN])),
):
    correlation_id = str(uuid.uuid4())
    qc_stream.emit_event(
        EventEnvelope(
            event_type=QCEventType.ERP_SYNC_REQUESTED,
            correlation_id=correlation_id,
            partition_key=inspection_id,
            payload={
                "inspection_id": inspection_id,
                "item_code": item_code,
                "verdict": verdict.value,
                "batch_number": batch_number,
            },
        )
    )

    try:
        res = await erpnext_adapter.sync_quality_inspection(
            inspection_id=inspection_id,
            item_code=item_code,
            batch_number=batch_number,
            verdict=verdict.value,
            defects_summary=["Automated Optical Inspection"],
        )
        doc_name = res.get("data", {}).get("name", "QI-2026-0001")
        qc_stream.emit_event(
            EventEnvelope(
                event_type=QCEventType.ERP_SYNC_COMPLETED,
                correlation_id=correlation_id,
                partition_key=inspection_id,
                payload={"inspection_id": inspection_id, "erp_doc_name": doc_name},
            )
        )
        return {"status": "SYNCED_TO_ERPNEXT", "erp_record": res}
    except Exception as e:
        qc_stream.emit_event(
            EventEnvelope(
                event_type=QCEventType.ERP_SYNC_FAILED,
                correlation_id=correlation_id,
                partition_key=inspection_id,
                payload={
                    "inspection_id": inspection_id,
                    "error_code": "ERP_SYNC_EXCEPTION",
                    "error_message": str(e),
                },
            )
        )
        raise HTTPException(status_code=500, detail=f"ERP sync error: {e}")


@router.get("/inspections/{inspection_id}/events")
async def get_inspection_events(inspection_id: str, user: UserContext = Depends(get_current_user)):
    return {"inspection_id": inspection_id, "events": qc_stream.get_events_for_inspection(inspection_id)}


@router.get("/sop/{defect_name}")
async def get_sop_guidance(defect_name: str, user: UserContext = Depends(get_current_user)):
    explanation = safety_gate.explain_defect_sop(defect_name, verdict="ADVISORY")
    return {"defect_name": defect_name, "sop_explanation": explanation}


@router.get("/models/active")
async def get_active_model_info():
    return model_registry.get_active_model()
