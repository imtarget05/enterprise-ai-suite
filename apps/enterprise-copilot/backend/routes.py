"""
FastAPI Routes for Project 1 (Enterprise Copilot).
Implements Chat, Workflow Checkpointing, Maker-Checker Approvals,
Shared ERPNext Sync, and Salesforce Adapter queries (Accounts, Leads, Opportunities).
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from packages.auth_integration.security import (
    UserContext, UserRole, enforce_maker_checker_rule, enforce_tenant_isolation, get_current_user, require_roles
)
from packages.shared_contracts.events import (
    BusinessEventEnvelope, BusinessEventType
)
from packages.erpnext_adapter.client import erpnext_adapter
from integrations.salesforce.adapter import salesforce_adapter
from apps.enterprise_copilot.backend.config import settings
from apps.enterprise_copilot.backend.llm_provider import llm_client
from apps.enterprise_copilot.backend.rabbitmq import rabbitmq_broker
from apps.enterprise_copilot.workflows.graph import copilot_graph
from packages.observability.telemetry import telemetry

router = APIRouter(prefix="/v1", tags=["Copilot"])


class ChatRequest(BaseModel):
    query: str
    tenant_id: Optional[str] = "TENANT-001"


class ApprovalRequest(BaseModel):
    action: str  # "APPROVED" or "REJECTED"
    supervisor_pin: str
    notes: Optional[str] = None


@router.post("/chat")
async def chat_endpoint(req: ChatRequest, user: UserContext = Depends(get_current_user)):
    enforce_tenant_isolation(user, req.tenant_id or user.tenant_id)
    with telemetry.trace_span("copilot.chat", user.user_id, {"tenant_id": req.tenant_id, "query_len": len(req.query)}):
        state = await copilot_graph.run(
            query=req.query,
            user_id=user.user_id,
            tenant_id=req.tenant_id or user.tenant_id,
        )
    return {
        "workflow_id": state.workflow_id,
        "requires_approval": state.requires_approval,
        "approval_status": state.approval_status,
        "current_state": state.current_state,
        "draft_order": state.draft_order,
        "response": state.response_text,
        "retrieved_sources": len(state.retrieved_docs),
        "citations": state.retrieved_docs,
        "audit_trail": state.audit_trail,
    }


@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    user: UserContext = Depends(get_current_user),
):
    checkpoint = copilot_graph.checkpoints.get(workflow_id)
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Workflow checkpoint not found.")
    enforce_tenant_isolation(user, checkpoint.tenant_id)
    return checkpoint.model_dump()


@router.post("/workflows/{workflow_id}/approve")
async def approve_workflow(
    workflow_id: str,
    req: ApprovalRequest,
    user: UserContext = Depends(require_roles([UserRole.CHECKER, UserRole.SYSTEM_ADMIN])),
):
    if req.supervisor_pin != "123456":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid supervisor authorization PIN.",
        )

    checkpoint = copilot_graph.checkpoints.get(workflow_id)
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Workflow checkpoint not found.")

    # Security ABAC & RBAC enforcement
    enforce_tenant_isolation(user, checkpoint.tenant_id)
    enforce_maker_checker_rule(maker_id=checkpoint.user_id, checker_id=user.user_id)

    try:
        approved = req.action.upper() == "APPROVED"
        state = copilot_graph.resume_approval(workflow_id, checker_id=user.user_id, approved=approved)
    except KeyError:
        raise HTTPException(status_code=404, detail="Workflow checkpoint not found.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if approved and state.draft_order:
        event = BusinessEventEnvelope(
            event_type=BusinessEventType.ORDER_APPROVED,
            correlation_id=workflow_id,
            tenant_id=state.tenant_id,
            maker_id=state.user_id,
            checker_id=user.user_id,
            payload=state.draft_order,
        )
        await rabbitmq_broker.publish_event(event)

        erp_res = await erpnext_adapter.create_sales_order(
            customer=state.draft_order.get("customer_name", "Acme"),
            items=[{
                "item_code": state.draft_order.get("item_code", "ALU-CNC-001"),
                "qty": state.draft_order.get("quantity", 500),
                "rate": state.draft_order.get("rate", 25.0),
            }],
            external_id=state.draft_order.get("order_id", workflow_id),
        )
        erp_record = erp_res.get("data", erp_res) if isinstance(erp_res, dict) else erp_res
        if isinstance(erp_record, dict) and "doc_type" not in erp_record:
            erp_record["doc_type"] = "Sales Order"
        state.erp_record = erp_record
        return {
            "status": "APPROVED_AND_POSTED",
            "erp_record": erp_record,
            "workflow": state.model_dump(),
        }

    return {"status": "REJECTED", "workflow": state.model_dump()}


@router.get("/erp/items/{item_code}")
async def get_erp_item(item_code: str, user: UserContext = Depends(get_current_user)):
    item = await erpnext_adapter.get_item(item_code)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_code} not found in ERPNext.")
    return item


@router.get("/salesforce/accounts/{external_id}")
async def get_salesforce_account(external_id: str, user: UserContext = Depends(get_current_user)):
    acc = await salesforce_adapter.get_account_by_external_id(external_id)
    if not acc:
        raise HTTPException(status_code=404, detail=f"Account with external ID {external_id} not found in Salesforce.")
    return acc


@router.get("/salesforce/leads")
async def query_salesforce_leads(
    company: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(10, le=50),
    user: UserContext = Depends(get_current_user),
):
    leads = await salesforce_adapter.query_leads(company=company, status=status, limit=limit)
    return {"total": len(leads), "leads": leads}


@router.get("/salesforce/leads/{external_id}")
async def get_salesforce_lead(external_id: str, user: UserContext = Depends(get_current_user)):
    lead = await salesforce_adapter.get_lead_by_external_id(external_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead with external ID {external_id} not found in Salesforce.")
    return lead


@router.get("/salesforce/opportunities")
async def query_salesforce_opportunities(
    account_id: Optional[str] = Query(None),
    stage_name: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    limit: int = Query(10, le=50),
    user: UserContext = Depends(get_current_user),
):
    opps = await salesforce_adapter.query_opportunities(
        account_id=account_id, stage_name=stage_name, min_amount=min_amount, limit=limit
    )
    return {"total": len(opps), "opportunities": opps}


@router.get("/salesforce/opportunities/{external_id}")
async def get_salesforce_opportunity(external_id: str, user: UserContext = Depends(get_current_user)):
    opp = await salesforce_adapter.get_opportunity_by_external_id(external_id)
    if not opp:
        raise HTTPException(status_code=404, detail=f"Opportunity with external ID {external_id} not found in Salesforce.")
    return opp


@router.get("/diagnostics/cost")
async def cost_diagnostics(user: UserContext = Depends(require_roles([UserRole.SYSTEM_ADMIN, UserRole.AUDITOR]))):
    return {
        "active_provider": llm_client.mode.value,
        "monthly_budget_usd": settings.MONTHLY_BUDGET_USD,
        "accumulated_spend_usd": llm_client.accumulated_spend_usd,
        "tokens_consumed": llm_client.accumulated_tokens,
        "qdrant_target": settings.QDRANT_URL,
        "erpnext_target": settings.ERPNEXT_URL,
        "profile": settings.PROFILE.value,
    }
