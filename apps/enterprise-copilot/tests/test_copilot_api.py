import pytest
from fastapi.testclient import TestClient
from packages.auth_integration.security import UserContext, UserRole, create_access_token
from apps.enterprise_copilot.backend.main import app
from integrations.salesforce.adapter import salesforce_adapter
from packages.erpnext_adapter.client import erpnext_client


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def maker_token():
    user = UserContext(
        user_id="maker-1",
        username="maker_test",
        email="maker@test.local",
        roles=[UserRole.MAKER],
        tenant_id="TENANT-001",
        facility_id="FAC-01",
        department="OPERATIONS",
    )
    return create_access_token(user)


@pytest.fixture
def checker_token():
    user = UserContext(
        user_id="checker-1",
        username="checker_test",
        email="checker@test.local",
        roles=[UserRole.CHECKER],
        tenant_id="TENANT-001",
        facility_id="FAC-01",
        department="SUPERVISION",
    )
    return create_access_token(user)


def test_copilot_health(client):
    res = client.get("/api/copilot/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_copilot_chat_rag_query(client, maker_token):
    res = client.post(
        "/api/copilot/v1/chat",
        headers={"Authorization": f"Bearer {maker_token}"},
        json={"query": "Kiểm tra quy định mua hàng và đặt hàng nhôm", "tenant_id": "TENANT-001"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert data["retrieved_sources"] > 0


def test_salesforce_adapter_query():
    import asyncio
    acc = asyncio.run(salesforce_adapter.get_account_by_external_id("CUST-ACME-01"))
    assert acc is not None
    assert acc["Name"] == "Acme Manufacturing Corp"


def test_erpnext_item_lookup():
    import asyncio
    item = asyncio.run(erpnext_client.get_item("ALU-CNC-001"))
    assert item is not None
    assert item["actual_qty"] > 0
