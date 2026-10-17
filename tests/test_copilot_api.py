import pytest
import asyncio
from fastapi.testclient import TestClient
from packages.auth_integration.security import UserContext, UserRole, create_access_token
from apps.enterprise_copilot.backend.main import app
from apps.enterprise_copilot.workflows.graph import copilot_graph
from apps.enterprise_copilot.rag.hybrid_retriever import hybrid_retriever
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


@pytest.fixture
def maker_checker_self_token():
    # Rogue user with both roles trying to self-approve
    user = UserContext(
        user_id="maker-1",
        username="maker_test",
        email="maker@test.local",
        roles=[UserRole.MAKER, UserRole.CHECKER],
        tenant_id="TENANT-001",
        facility_id="FAC-01",
        department="OPERATIONS",
    )
    return create_access_token(user)


@pytest.fixture
def foreign_tenant_checker_token():
    # Checker belonging to TENANT-002 trying to approve TENANT-001 workflow
    user = UserContext(
        user_id="checker-tenant-2",
        username="checker_t2",
        email="checker@tenant2.local",
        roles=[UserRole.CHECKER],
        tenant_id="TENANT-002",
        facility_id="FAC-02",
        department="SUPERVISION",
    )
    return create_access_token(user)


def test_copilot_health(client):
    res = client.get("/api/copilot/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert data["salesforce_sandbox"] is True


def test_copilot_chat_rag_query(client, maker_token):
    res = client.post(
        "/api/copilot/v1/chat",
        headers={"Authorization": f"Bearer {maker_token}"},
        json={"query": "Kiểm tra quy định mua hàng và tồn kho", "tenant_id": "TENANT-001"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert data["retrieved_sources"] > 0
    assert "citations" in data
    assert len(data["citations"]) > 0
    assert "score" in data["citations"][0]


def test_hitl_approval_flow_valid_pin(client, maker_token, checker_token):
    chat_res = client.post(
        "/api/copilot/v1/chat",
        headers={"Authorization": f"Bearer {maker_token}"},
        json={
            "query": "Tạo đơn hàng đặt hàng 500 linh kiện nhôm CNC mã ALU-CNC-001",
            "tenant_id": "TENANT-001",
        },
    )
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert data["requires_approval"] is True
    assert data["approval_status"] == "PENDING_APPROVAL"
    assert data["draft_order"]["total_amount"] >= 10000.0
    workflow_id = data["workflow_id"]

    approve_res = client.post(
        f"/api/copilot/v1/workflows/{workflow_id}/approve",
        headers={"Authorization": f"Bearer {checker_token}"},
        json={"action": "APPROVED", "supervisor_pin": "123456", "notes": "Approved for production"},
    )
    assert approve_res.status_code == 200
    app_data = approve_res.json()
    assert app_data["status"] == "APPROVED_AND_POSTED"
    assert app_data["erp_record"]["doc_type"] == "Sales Order"
    assert app_data["workflow"]["approval_status"] == "APPROVED"


def test_hitl_approval_flow_invalid_pin(client, maker_token, checker_token):
    chat_res = client.post(
        "/api/copilot/v1/chat",
        headers={"Authorization": f"Bearer {maker_token}"},
        json={"query": "Đặt hàng 500 linh kiện nhôm CNC", "tenant_id": "TENANT-001"},
    )
    assert chat_res.status_code == 200
    workflow_id = chat_res.json()["workflow_id"]

    approve_res = client.post(
        f"/api/copilot/v1/workflows/{workflow_id}/approve",
        headers={"Authorization": f"Bearer {checker_token}"},
        json={"action": "APPROVED", "supervisor_pin": "000000"},
    )
    assert approve_res.status_code == 400
    assert "Invalid supervisor authorization PIN" in approve_res.json()["detail"]


def test_anti_fraud_self_approval_prevented(client, maker_token, maker_checker_self_token):
    chat_res = client.post(
        "/api/copilot/v1/chat",
        headers={"Authorization": f"Bearer {maker_token}"},
        json={"query": "Tạo đơn hàng đặt hàng nhôm", "tenant_id": "TENANT-001"},
    )
    assert chat_res.status_code == 200
    workflow_id = chat_res.json()["workflow_id"]

    approve_res = client.post(
        f"/api/copilot/v1/workflows/{workflow_id}/approve",
        headers={"Authorization": f"Bearer {maker_checker_self_token}"},
        json={"action": "APPROVED", "supervisor_pin": "123456"},
    )
    assert approve_res.status_code == 400
    assert "Maker-Checker" in approve_res.json()["detail"]


def test_tenant_isolation_enforcement(client, maker_token, foreign_tenant_checker_token):
    chat_res = client.post(
        "/api/copilot/v1/chat",
        headers={"Authorization": f"Bearer {maker_token}"},
        json={"query": "Đặt hàng vật tư CNC", "tenant_id": "TENANT-001"},
    )
    assert chat_res.status_code == 200
    workflow_id = chat_res.json()["workflow_id"]

    approve_res = client.post(
        f"/api/copilot/v1/workflows/{workflow_id}/approve",
        headers={"Authorization": f"Bearer {foreign_tenant_checker_token}"},
        json={"action": "APPROVED", "supervisor_pin": "123456"},
    )
    assert approve_res.status_code == 403
    assert "Cross-tenant access forbidden" in approve_res.json()["detail"]

    cross_chat = client.post(
        "/api/copilot/v1/chat",
        headers={"Authorization": f"Bearer {maker_token}"},
        json={"query": "Tra cứu", "tenant_id": "TENANT-999"},
    )
    assert cross_chat.status_code == 403


def test_langgraph_five_states_execution():
    assert copilot_graph.STATES == [
        "retrieve_context",
        "evaluate_policy",
        "generate_draft",
        "require_approval",
        "post_to_erp",
    ]

    async def _test():
        state = await copilot_graph.run("Tạo đơn hàng nhôm CNC", "maker-user", "TENANT-001")
        assert state.requires_approval is True
        assert state.current_state == "require_approval"
        logged_states = [entry["state"] for entry in state.audit_trail]
        assert "retrieve_context" in logged_states
        assert "evaluate_policy" in logged_states
        assert "generate_draft" in logged_states
        assert "require_approval" in logged_states

        resumed = copilot_graph.resume_approval(state.workflow_id, "checker-user", approved=True)
        assert resumed.approval_status == "APPROVED"
        assert resumed.erp_record is not None
        assert "post_to_erp" in [entry["state"] for entry in resumed.audit_trail]

    asyncio.run(_test())


def test_salesforce_adapter_lead_and_opportunity():
    async def _test():
        acc = await salesforce_adapter.get_account_by_external_id("CUST-ACME-01")
        assert acc is not None
        assert acc["Name"] == "Acme Manufacturing Corp"

        lead = await salesforce_adapter.get_lead_by_external_id("LEAD-ACME-01")
        assert lead is not None
        assert lead["Company"] == "Acme Manufacturing Corp"

        leads = await salesforce_adapter.query_leads(company="Acme")
        assert len(leads) >= 1

        opp = await salesforce_adapter.get_opportunity_by_external_id("OPP-ACME-01")
        assert opp is not None
        assert opp["Amount"] == 12500.0

        opps = await salesforce_adapter.query_opportunities(min_amount=10000.0)
        assert len(opps) >= 2

    asyncio.run(_test())


def test_salesforce_api_endpoints(client, maker_token):
    res_lead = client.get(
        "/api/copilot/v1/salesforce/leads/LEAD-ACME-01",
        headers={"Authorization": f"Bearer {maker_token}"},
    )
    assert res_lead.status_code == 200
    assert res_lead.json()["ERP_External_ID__c"] == "LEAD-ACME-01"

    res_opp = client.get(
        "/api/copilot/v1/salesforce/opportunities/OPP-ACME-01",
        headers={"Authorization": f"Bearer {maker_token}"},
    )
    assert res_opp.status_code == 200
    assert res_opp.json()["Amount"] == 12500.0


def test_erpnext_item_lookup():
    async def _test():
        item = await erpnext_client.get_item("ALU-CNC-001")
        assert item is not None
        assert item["actual_qty"] > 0

    asyncio.run(_test())
