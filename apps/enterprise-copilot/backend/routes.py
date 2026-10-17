"""
FastAPI Routes for Project 1 (Enterprise Copilot).
Implements Chat, Workflow Checkpointing, Maker-Checker Approvals,
Shared ERPNext Sync, and Salesforce Adapter queries.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
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
    state = await copilot_graph.run(
        query=req.query,
        user_id=user.user_id,
        tenant_id=req.tenant_id or user.tenant_id,
    )
    return {
        "workflow_id": state.workflow_id,
        "requires_approval": state.requires_approval,
        "approval_status": state.approval_status,
        "draft_order": state.draft_order,
        "response": state.response_text,
        "retrieved_sources": len(state.retrieved_docs),
    }


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
        return {
            "status": "APPROVED_AND_POSTED",
            "erp_record": erp_res,
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
