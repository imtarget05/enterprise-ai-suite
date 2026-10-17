"""
Shared ERPNext v15 Adapter Reused Across Project 1 & Project 2.
Provides unified REST API connectivity for:
- Sales Order, Items, Customers (Project 1: Copilot)
- Quality Inspection, Stock Ledger, Quarantine (Project 2: Visual Quality Gate)
"""

from typing import Any, Dict, List, Optional
import httpx


class SharedERPNextAdapter:
    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: str = "demo_erp_api_key",
        api_secret: str = "demo_erp_api_secret",
        use_sandbox: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"token {api_key}:{api_secret}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.use_sandbox = use_sandbox
        
        # High-Fidelity In-Memory Sandbox Stores
        self._items = {
            "ALU-CNC-001": {
                "name": "ALU-CNC-001",
                "item_name": "Linh kiện Nhôm CNC Chuẩn",
                "stock_uom": "Nos",
                "actual_qty": 1240.0,
                "standard_rate": 25.0,
            },
            "SCR-M4-02": {
                "name": "SCR-M4-02",
                "item_name": "Ốc vít M4 Thép Không Gỉ",
                "stock_uom": "Nos",
                "actual_qty": 45000.0,
                "standard_rate": 0.15,
            },
        }
        self._sales_orders = {}
        self._quality_inspections = {}

    async def ping(self) -> Dict[str, Any]:
        if self.use_sandbox:
            return {"status": "ok", "message": "ERPNext Sandbox Online", "version": "v15.0.0-sandbox"}
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self.base_url}/api/method/frappe.ping", headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    # --- PROJECT 1: Sales Order & Items ---
    async def get_item(self, item_code: str) -> Optional[Dict[str, Any]]:
        if self.use_sandbox:
            return self._items.get(item_code)
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self.base_url}/api/resource/Item/{item_code}", headers=self.headers)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json().get("data")

    async def create_sales_order(self, customer: str, items: List[Dict[str, Any]], external_id: str) -> Dict[str, Any]:
        if self.use_sandbox:
            if external_id in self._sales_orders:
                return {"data": self._sales_orders[external_id], "idempotent_replay": True}
            doc_name = f"SO-2026-{len(self._sales_orders) + 1:04d}"
            total = sum(i["qty"] * i["rate"] for i in items)
            record = {
                "name": doc_name,
                "customer": customer,
                "docstatus": 1,
                "items": items,
                "total": total,
                "grand_total": total,
                "external_id": external_id,
                "status": "Submitted",
            }
            self._sales_orders[external_id] = record
            return {"data": record, "idempotent_replay": False}

        payload = {"customer": customer, "items": items, "external_id": external_id, "docstatus": 1}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{self.base_url}/api/resource/Sales Order", headers=self.headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    # --- PROJECT 2: Quality Inspection ---
    async def sync_quality_inspection(
        self,
        inspection_id: str,
        item_code: str,
        batch_number: str,
        verdict: str,
        defects_summary: List[str],
    ) -> Dict[str, Any]:
        erp_status = "Accepted" if verdict == "PASSED" else "Rejected"
        if self.use_sandbox:
            if inspection_id in self._quality_inspections:
                return {"data": self._quality_inspections[inspection_id], "idempotent_replay": True}
            doc_name = f"QI-2026-{len(self._quality_inspections) + 1:04d}"
            record = {
                "name": doc_name,
                "inspection_type": "In Process",
                "reference_type": "Stock Entry",
                "item_code": item_code,
                "batch_no": batch_number,
                "status": erp_status,
                "remarks": "; ".join(defects_summary),
                "external_id": inspection_id,
            }
            self._quality_inspections[inspection_id] = record
            return {"data": record, "idempotent_replay": False}

        payload = {
            "inspection_type": "In Process",
            "item_code": item_code,
            "batch_no": batch_number,
            "status": erp_status,
            "remarks": "; ".join(defects_summary),
            "external_id": inspection_id,
            "docstatus": 1,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{self.base_url}/api/resource/Quality Inspection", headers=self.headers, json=payload)
            resp.raise_for_status()
            return resp.json()


erpnext_adapter = SharedERPNextAdapter()
erpnext_client = erpnext_adapter
