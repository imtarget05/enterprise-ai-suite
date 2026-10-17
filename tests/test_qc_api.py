import pytest
from fastapi.testclient import TestClient
from packages.auth_integration.security import UserContext, UserRole, create_access_token
from packages.shared_contracts.events import QualityVerdict
from apps.visual_quality_gate.backend.main import app
from apps.visual_quality_gate.backend.rules_engine import rules_engine
from apps.visual_quality_gate.backend.safety_gate import safety_gate
from packages.shared_contracts.events import BoundingBox, DefectSeverity


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def inspector_token():
    user = UserContext(
        user_id="insp-1",
        username="inspector_test",
        email="insp@test.local",
        roles=[UserRole.QC_INSPECTOR],
        tenant_id="TENANT-001",
        facility_id="FAC-01",
        department="QUALITY",
    )
    return create_access_token(user)


def test_qc_health(client):
    res = client.get("/api/qc/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_deterministic_safety_gate_quarantine_on_critical_defect():
    critical_defect = BoundingBox(
        x_min=0.1, y_min=0.1, x_max=0.3, y_max=0.3,
        class_id=0, class_name="surface_crack",
        confidence=0.92, severity=DefectSeverity.CRITICAL, area_ratio=0.04
    )
    res = safety_gate.decide_quality([critical_defect])
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
