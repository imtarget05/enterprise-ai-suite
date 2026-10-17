# PUBLIC DEMO & INGRESS ROUTING DIRECTORY

This document catalogs public routing endpoints, DNS mapping, health check probes, and credentials for testing both deployed products.

---

## 1. Public Frontend Endpoints (Cloudflare Pages)

| Application | Target Public URL | CDN / Host Provider | Authentication Required |
| :--- | :--- | :--- | :--- |
| **Product A (Enterprise Copilot)** | `https://enterprise-copilot.pages.dev` | Cloudflare Pages | Yes (Demo JWT / Mock SSO) |
| **Product B (Visual QC & Defect Inspection)** | `https://enterprise-qc.pages.dev` | Cloudflare Pages | Yes (Demo Inspector Role) |

*Local development mirrors:*
- Product A Frontend: `http://localhost:3000`
- Product B Frontend: `http://localhost:3001`

---

## 2. API Ingress & Reverse Proxy Routes (Nginx / Cloudflare Tunnel)

Base Domain: `https://api.enterprise-suite.demo` (or tunnel hostname)

| Route Path | Upstream Container | Protocol | Description |
| :--- | :--- | :--- | :--- |
| `/api/copilot/v1/*` | `copilot-api:8001` | HTTP/REST + SSE | Copilot chat, LangGraph stream, Salesforce adapter |
| `/api/copilot/health` | `copilot-api:8001` | HTTP/REST | Copilot liveness & readiness probe |
| `/api/qc/v1/*` | `qc-inspection-api:8002` | HTTP/REST + Multipart | QC image ingestion, ONNX inference, review verdict |
| `/api/qc/health` | `qc-inspection-api:8002` | HTTP/REST | QC pipeline liveness & model readiness probe |
| `/app/*` | `erpnext-web:8080` | HTTP/REST | ERPNext Desk web interface |
| `/api/method/*` | `erpnext-web:8080` | HTTP/REST | ERPNext standard REST API |

---

## 3. Demo Credentials (Zero-Leakage Sandbox)

Default test users pre-seeded into the database:

| Username / Email | Password | Role | Permissions |
| :--- | :--- | :--- | :--- |
| `maker@enterprise.local` | `DemoMaker2026!` | `MAKER` | Query knowledge base, draft Sales Orders, request QC sync |
| `checker@enterprise.local` | `DemoChecker2026!` | `CHECKER` | Approve orders, execute ERP ledger posts, override QC |
| `qc_inspector@enterprise.local`| `DemoQC2026!` | `QC_INSPECTOR` | Inspect parts, annotate defects, submit inspection verdict |
| `auditor@enterprise.local` | `DemoAuditor2026!` | `AUDITOR` | View read-only audit log, Langfuse trace viewer, provenance |
| `admin@enterprise.local` | `DemoAdmin2026!` | `SYSTEM_ADMIN` | Full administrative control across both suites |

---

## 4. Automated Health Verification Command

To verify ingress routing and all services in a single step:

```bash
# Run the public health verification script
python infra/scripts/verify_public_endpoints.py --base-url http://localhost:80
```
Expected output:
- `[PASS]` Product A Copilot API (`/api/copilot/health`) -> `status: "healthy", qdrant: "connected"`
- `[PASS]` Product B QC API (`/api/qc/health`) -> `status: "healthy", onnx_model: "loaded", redpanda: "connected"`
- `[PASS]` ERPNext API (`/api/method/frappe.ping`) -> `message: "pong"`
