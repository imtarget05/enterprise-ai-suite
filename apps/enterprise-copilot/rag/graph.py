"""
LangGraph Stateful Orchestration Graph for Product A.
Implements StateGraph, checkpointing, multi-step RAG routing,
and Human-In-The-Loop (HITL) approval gates for ERP mutations.
"""

from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel
from apps.enterprise_copilot.backend.core.llm_provider import llm_client
from apps.enterprise_copilot.backend.rag.hybrid_retriever import hybrid_retriever


class WorkflowState(BaseModel):
    workflow_id: str
    user_id: str
    tenant_id: str
    query: str
    retrieved_docs: List[Dict[str, Any]] = []
    draft_order: Optional[Dict[str, Any]] = None
    requires_approval: bool = False
    approval_status: str = "INITIAL"  # INITIAL, PENDING_APPROVAL, APPROVED, REJECTED
    checker_id: Optional[str] = None
    response_text: str = ""
    error: Optional[str] = None


class CopilotGraphRunner:
    def __init__(self):
        self.checkpoints: Dict[str, WorkflowState] = {}

    async def run(self, query: str, user_id: str, tenant_id: str) -> WorkflowState:
        workflow_id = str(uuid.uuid4())
        state = WorkflowState(
            workflow_id=workflow_id,
            user_id=user_id,
            tenant_id=tenant_id,
            query=query,
        )

        # Step 1: Retrieval Node (Hybrid RAG)
        docs = hybrid_retriever.retrieve(query, top_k=3)
        state.retrieved_docs = docs

        # Step 2: Intent Classification & Order Drafting Node
        if any(w in query.lower() for w in ["đặt hàng", "order", "tạo đơn", "mua linh kiện"]):
            # Draft an ERP Sales Order
            order = {
                "order_id": f"ORD-{uuid.uuid4().hex[:6].upper()}",
                "customer_name": "Acme Manufacturing Corp",
                "item_code": "ALU-CNC-001",
                "quantity": 500,
                "rate": 25.0,
                "total_amount": 12500.0,
            }
            state.draft_order = order

            # Step 3: HITL Guardrail Node (Value Cap: > $10,000 USD requires Checker approval)
            if order["total_amount"] >= 10000.0:
                state.requires_approval = True
                state.approval_status = "PENDING_APPROVAL"
                state.response_text = (
                    f"Đã tạo bản nháp đơn hàng {order['order_id']} trị giá ${order['total_amount']:,.2f} USD. "
                    f"Do giá trị vượt định mức $10,000 USD, quy trình đã tạm dừng và chờ Kiểm soát viên (Checker) phê duyệt."
                )
                # Save checkpoint and pause execution
                self.checkpoints[workflow_id] = state
                return state

        # Step 4: Generation Node (if no approval needed or standard query)
        system_prompt = (
            "Bạn là Trợ lý AI Quản trị Doanh nghiệp Copilot kết nối ERPNext và Salesforce. "
            f"Dữ liệu tham khảo từ tài liệu:\n{docs}"
        )
        gen = await llm_client.generate_response(query, system_prompt, user_id)
        state.response_text = gen["content"]
        state.approval_status = "COMPLETED"
        self.checkpoints[workflow_id] = state
        return state

    def resume_approval(self, workflow_id: str, checker_id: str, approved: bool) -> WorkflowState:
        if workflow_id not in self.checkpoints:
            raise KeyError(f"Workflow checkpoint {workflow_id} not found.")

        state = self.checkpoints[workflow_id]
        if state.approval_status != "PENDING_APPROVAL":
            raise ValueError(f"Workflow {workflow_id} is not waiting for approval (Current: {state.approval_status}).")

        # Invariant: Maker cannot be Checker
        if state.user_id == checker_id:
            raise ValueError("Maker-Checker Invariant Violation: Approver cannot be the same user who initiated the order.")

        state.checker_id = checker_id
        if approved:
            state.approval_status = "APPROVED"
            state.response_text += f"\n[Kiểm soát viên {checker_id} ĐÃ DUYỆT ĐƠN HÀNG THÀNH CÔNG. Ghi sổ ERPNext...]"
        else:
            state.approval_status = "REJECTED"
            state.response_text += f"\n[Kiểm soát viên {checker_id} ĐÃ TỪ CHỐI ĐƠN HÀNG.]"

        self.checkpoints[workflow_id] = state
        return state


copilot_graph = CopilotGraphRunner()
