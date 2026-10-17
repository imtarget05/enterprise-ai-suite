"""
Comprehensive Quality Control API, Safety Gate & Event Pipeline Test Suite.
Verifies:
1. Deterministic Safety Gate rules & edge cases (boundary ratios, multi-defect combinations, zero-LLM isolation).
2. ONNX CPU inference latency SLA (< 200ms SLA, < 80ms target).
3. Redpanda 8-event lifecycle emission with correlation IDs and SHA-256 idempotency keys.
4. Manual inspector override with mandatory audit reason notes.
5. ERPNext Quality Inspection sync with readings/parameters, failure handling, and retry tracking.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from packages.auth_integration.security import UserContext, UserRole, create_access_token
from packages.shared_contracts.events import (
    BoundingBox, DefectSeverity, EventEnvelope, QCEventType, QualityVerdict
)
from apps.visual_quality_gate.backend.main import app
from apps.visual_quality_gate.backend.rules_engine import QCRulesConfig, QCRulesEngine, rules_engine
from apps.visual_quality_gate.backend.safety_gate import safety_gate
from apps.visual_quality_gate.inference.onnx_infer import onnx_detector
from apps.visual_quality_gate.event_consumers.redpanda_stream import qc_stream
from packages.erpnext_adapter.client import erpnext_adapter


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def inspector_token():
    user = UserContext(
        user_id="insp-007",
        username="lead_qc_inspector",
        email="qc_lead@factory.internal",
        roles=[UserRole.QC_INSPECTOR],
        tenant_id="TENANT-001",
        facility_id="FACILITY-HAIPHONG-01",
        department="QUALITY_ASSURANCE",
    )
    return create_access_token(user)


@pytest.fixture
def unauthorized_token():
    user = UserContext(
        user_id="viewer-999",
        username="guest_viewer",
        email="viewer@external.local",
        roles=[UserRole.VIEWER],
        tenant_id="TENANT-001",
        facility_id="FACILITY-HAIPHONG-01",
    )
    return create_access_token(user)


# ---------------------------------------------------------------------------
# 1. Health & Configuration
# ---------------------------------------------------------------------------

def test_qc_health(client):
    res = client.get("/api/qc/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "active_model" in data
    assert data["service"] == "Project 2 - Visual Quality Gate"


# ---------------------------------------------------------------------------
# 2. Deterministic Safety Gate: LLM Isolation & Core Rules
# ---------------------------------------------------------------------------

def test_deterministic_safety_gate_quarantine_on_critical_crack():
    crack = BoundingBox(
        x_min=0.20, y_min=0.20, x_max=0.35, y_max=0.35,
        class_id=0, class_name="surface_crack",
        confidence=0.91, severity=DefectSeverity.CRITICAL, area_ratio=0.022
    )
    res = safety_gate.decide_quality([crack])
    assert res["verdict"] == QualityVerdict.QUARANTINE.value
    assert res["llm_involved"] is False
    assert res["engine"] == "deterministic_safety_gate"
    assert any("CRITICAL DEFECT DETECTED" in r for r in res["reasons"])


def test_deterministic_safety_gate_quarantine_on_structural_porosity():
    porosity = BoundingBox(
        x_min=0.40, y_min=0.40, x_max=0.45, y_max=0.45,
        class_id=4, class_name="structural_porosity",
        confidence=0.85, severity=DefectSeverity.CRITICAL, area_ratio=0.0025
    )
    res = safety_gate.decide_quality([porosity])
    assert res["verdict"] == QualityVerdict.QUARANTINE.value
    assert res["llm_involved"] is False
    assert any("CRITICAL DEFECT DETECTED" in r for r in res["reasons"])


def test_deterministic_safety_gate_pass_on_negligible_defect():
    minor_defect = BoundingBox(
        x_min=0.1, y_min=0.1, x_max=0.12, y_max=0.12,
        class_id=3, class_name="color_defect",
        confidence=0.55, severity=DefectSeverity.NEGLIGIBLE, area_ratio=0.0004
    )
    res = safety_gate.decide_quality([minor_defect])
    assert res["verdict"] == QualityVerdict.PASSED.value
    assert res["llm_involved"] is False


# ---------------------------------------------------------------------------
# 3. Deterministic Safety Gate: Boundary Ratios & Combinations
# ---------------------------------------------------------------------------

def test_safety_gate_area_ratio_boundary_conditions():
    # Exactly 3.0% area ratio (boundary) -> PASSED
    box_boundary = BoundingBox(
        x_min=0.0, y_min=0.0, x_max=0.3, y_max=0.1,
        class_id=2, class_name="dent_scratch",
        confidence=0.70, severity=DefectSeverity.MINOR, area_ratio=0.0300
    )
    res_boundary = safety_gate.decide_quality([box_boundary])
    assert res_boundary["verdict"] == QualityVerdict.PASSED.value

    # 3.01% area ratio (just above 3% threshold) -> QUARANTINE
    box_exceeded = BoundingBox(
        x_min=0.0, y_min=0.0, x_max=0.31, y_max=0.1,
        class_id=2, class_name="dent_scratch",
        confidence=0.70, severity=DefectSeverity.MINOR, area_ratio=0.0301
    )
    res_exceeded = safety_gate.decide_quality([box_exceeded])
    assert res_exceeded["verdict"] == QualityVerdict.QUARANTINE.value
    assert any("DEFECT AREA LIMIT EXCEEDED" in r for r in res_exceeded["reasons"])


def test_safety_gate_multi_defect_combination_area_sum():
    # Two minor defects: 1.8% + 1.5% = 3.3% (> 3.0% threshold) -> QUARANTINE
    box1 = BoundingBox(
        x_min=0.1, y_min=0.1, x_max=0.2, y_max=0.28,
        class_id=2, class_name="dent_scratch",
        confidence=0.65, severity=DefectSeverity.MINOR, area_ratio=0.0180
    )
    box2 = BoundingBox(
        x_min=0.5, y_min=0.5, x_max=0.6, y_max=0.65,
        class_id=2, class_name="dent_scratch",
        confidence=0.60, severity=DefectSeverity.MINOR, area_ratio=0.0150
    )
    res = safety_gate.decide_quality([box1, box2])
    assert res["verdict"] == QualityVerdict.QUARANTINE.value
    assert res["rule_evaluations"]["total_area_ratio"] == 0.0330


def test_safety_gate_filters_low_confidence_noise():
    # Critical label but confidence 0.35 (< 0.40 threshold) -> ignored, part passes
    noise_box = BoundingBox(
        x_min=0.1, y_min=0.1, x_max=0.2, y_max=0.2,
        class_id=0, class_name="surface_crack",
        confidence=0.35, severity=DefectSeverity.CRITICAL, area_ratio=0.01
    )
    res = safety_gate.decide_quality([noise_box])
    assert res["verdict"] == QualityVerdict.PASSED.value
    assert res["rule_evaluations"]["critical_count"] == 0


def test_safety_gate_excessive_major_defects():
    # 2 Major defects exceeds max_major_defects (1) -> QUARANTINE
    major1 = BoundingBox(
        x_min=0.1, y_min=0.1, x_max=0.2, y_max=0.2,
        class_id=1, class_name="void_cavity",
        confidence=0.75, severity=DefectSeverity.MAJOR, area_ratio=0.01
    )
    major2 = BoundingBox(
        x_min=0.4, y_min=0.4, x_max=0.5, y_max=0.5,
        class_id=1, class_name="void_cavity",
        confidence=0.78, severity=DefectSeverity.MAJOR, area_ratio=0.01
    )
    res = safety_gate.decide_quality([major1, major2])
    assert res["verdict"] == QualityVerdict.QUARANTINE.value
    assert any("MAJOR DEFECT COUNT EXCEEDED" in r for r in res["reasons"])


# ---------------------------------------------------------------------------
# 4. Latency SLA Compliance (< 200ms SLA, < 80ms target)
# ---------------------------------------------------------------------------

def test_onnx_inference_latency_sla():
    dummy_bytes = b"INSPECTION_CALIBRATION_PAYLOAD_TEST_12345"
    # Pre-test warmup pass
    onnx_detector.infer_image(dummy_bytes)
    latencies = []
    for _ in range(5):
        boxes, lat_ms = onnx_detector.infer_image(dummy_bytes)
        latencies.append(lat_ms)
        assert lat_ms < 200.0, f"Inference exceeded 200ms SLA: {lat_ms} ms"

    median_lat = sorted(latencies)[len(latencies) // 2]
    assert median_lat < 100.0, f"Expected median latency < 100ms on CPU, got {median_lat} ms"


def test_qc_inspection_endpoint(client, inspector_token):
    sample_bytes = b"SAMPLE_INSPECTION_PAYLOAD_ALUMINUM_PART_2026"
    files = {"file": ("test_part.jpg", sample_bytes, "image/jpeg")}
    data = {"item_code": "ALU-CNC-001", "batch_number": "BATCH-TEST", "work_order_id": "WO-99"}

    res = client.post(
        "/api/qc/v1/inspections",
        headers={"Authorization": f"Bearer {inspector_token}"},
        files=files,
        data=data,
    )
    assert res.status_code == 200
    d = res.json()
    assert "inspection_id" in d
    assert d["latency_ms"] < 200.0  # CPU inference SLA guarantee
    assert "verdict" in d
    assert "reasons" in d
    assert "defects" in d


# ---------------------------------------------------------------------------
# 5. Manual Inspector Override with Mandatory Audit Notes
# ---------------------------------------------------------------------------

def test_manual_inspector_override_requires_mandatory_notes(client, inspector_token):
    insp_id = "INSP-TEST-OVERRIDE-01"

    # Attempt override without audit notes -> 400 Bad Request
    res_empty = client.post(
        f"/api/qc/v1/inspections/{insp_id}/review",
        headers={"Authorization": f"Bearer {inspector_token}"},
        json={
            "action": "OVERRIDE_VERDICT",
            "override_verdict": "PASSED",
            "notes": "",
        },
    )
    assert res_empty.status_code == 400
    assert "Mandatory audit reason" in res_empty.json()["detail"]


def test_manual_inspector_override_success_and_event_emission(client, inspector_token):
    insp_id = "INSP-TEST-OVERRIDE-02"
    audit_notes = "Non-destructive eddy current testing confirmed crack is superficial tooling smudge < 0.05mm."

    res = client.post(
        f"/api/qc/v1/inspections/{insp_id}/review",
        headers={"Authorization": f"Bearer {inspector_token}"},
        json={
            "action": "OVERRIDE_VERDICT",
            "override_verdict": "PASSED",
            "notes": audit_notes,
        },
    )
    assert res.status_code == 200
    d = res.json()
    assert d["status"] == "REVIEW_RECORDED"
    assert d["override_verdict"] == "PASSED"

    # Verify event emission in Redpanda stream
    events = qc_stream.get_events_for_inspection(insp_id)
    review_evs = [e for e in events if e.get("event_type") == QCEventType.REVIEW_COMPLETED.value]
    assert len(review_evs) >= 1
    latest_review = review_evs[-1]
    assert latest_review["payload"]["action"] == "OVERRIDE_VERDICT"
    assert latest_review["payload"]["review_notes"] == audit_notes
    assert len(latest_review["idempotency_key"]) == 64  # SHA-256


# ---------------------------------------------------------------------------
# 6. ERPNext Sync: Parameters, Readings, Failure & Retry Handling
# ---------------------------------------------------------------------------

def test_erpnext_sync_with_parameters_and_idempotency(client, inspector_token):
    insp_id = "INSP-ERP-TEST-001"
    custom_readings = [
        {
            "specification": "Surface Crack & Porosity",
            "acceptance_criteria": "Zero critical defects",
            "reading_1": "Conformant",
            "status": "Accepted",
        },
        {
            "specification": "Defect Area Ratio",
            "acceptance_criteria": "<= 3.00%",
            "reading_1": "0.4%",
            "status": "Accepted",
        },
    ]

    # Initial sync
    res = client.post(
        f"/api/qc/v1/inspections/{insp_id}/sync-erp",
        headers={"Authorization": f"Bearer {inspector_token}"},
        params={"item_code": "ALU-CNC-001", "batch_number": "BATCH-2026-X1", "verdict": "PASSED"},
        json={"inspection_parameters": custom_readings},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SYNCED_TO_ERPNEXT"
    erp_doc = data["erp_record"]["data"]
    assert "readings" in erp_doc
    assert erp_doc["readings"][0]["specification"] == "Surface Crack & Porosity"

    # Verify idempotency on second call
    res_replay = client.post(
        f"/api/qc/v1/inspections/{insp_id}/sync-erp",
        headers={"Authorization": f"Bearer {inspector_token}"},
        params={"item_code": "ALU-CNC-001", "batch_number": "BATCH-2026-X1", "verdict": "PASSED"},
    )
    assert res_replay.status_code == 200
    assert res_replay.json()["erp_record"]["idempotent_replay"] is True


def test_erpnext_sync_failure_and_retry_emission(client, inspector_token):
    insp_id = "INSP-ERP-FAIL-001"

    # Mock ERP failure
    with patch.object(erpnext_adapter, "sync_quality_inspection", side_effect=RuntimeError("ERP Gateway Connection Refused")):
        res_fail = client.post(
            f"/api/qc/v1/inspections/{insp_id}/sync-erp",
            headers={"Authorization": f"Bearer {inspector_token}"},
            params={"item_code": "ALU-CNC-001", "batch_number": "BATCH-FAIL", "verdict": "QUARANTINE", "retry_count": 0},
        )
        assert res_fail.status_code == 500
        assert "ERP sync error" in res_fail.json()["detail"]

    # Verify failure event was emitted
    events = qc_stream.get_events_for_inspection(insp_id)
    fail_evs = [e for e in events if e.get("event_type") == QCEventType.ERP_SYNC_FAILED.value]
    assert len(fail_evs) >= 1
    assert fail_evs[-1]["payload"]["error_code"] == "ERP_SYNC_EXCEPTION"
    assert "Connection Refused" in fail_evs[-1]["payload"]["error_message"]

    # Simulate successful retry with retry_count = 1
    res_retry = client.post(
        f"/api/qc/v1/inspections/{insp_id}/sync-erp",
        headers={"Authorization": f"Bearer {inspector_token}"},
        params={"item_code": "ALU-CNC-001", "batch_number": "BATCH-FAIL", "verdict": "QUARANTINE", "retry_count": 1},
    )
    assert res_retry.status_code == 200
    assert res_retry.json()["retry_count"] == 1

    events_after = qc_stream.get_events_for_inspection(insp_id)
    success_evs = [e for e in events_after if e.get("event_type") == QCEventType.ERP_SYNC_COMPLETED.value]
    assert len(success_evs) >= 1
    assert success_evs[-1]["retry_count"] == 1
