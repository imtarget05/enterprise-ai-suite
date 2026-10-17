# NETWORK SECURITY & ACCESS CONTROL SPECIFICATION

This document outlines the defense-in-depth network security architecture, ingress filtering, authentication mechanisms, and privilege hardening across the Enterprise AI Suite.

---

## 1. Port Hardening & Perimeter Defense

| Port | Service | Exposure Level | Binding Interface | Security Rule |
| :--- | :--- | :--- | :--- | :--- |
| **80** | HTTP | Public | `0.0.0.0:80` | Auto-redirect to HTTPS (301 Moved Permanently) |
| **443** | HTTPS | Public | `0.0.0.0:443` | TLS 1.2 / 1.3 only, HSTS enabled, TLS cert via Cloudflare / Let's Encrypt |
| **22** | SSH | Restricted | `0.0.0.0:22` | Key-based authentication only, root login disabled |
| **8001** | Product A API | Internal Only | `127.0.0.1:8001` / Docker Net | Routed only through Nginx `/api/copilot/` |
| **8002** | Product B API | Internal Only | `127.0.0.1:8002` / Docker Net | Routed only through Nginx `/api/qc/` |
| **8080** | ERPNext Web | Internal Only | `127.0.0.1:8080` / Docker Net | Routed only through Nginx `/app/` |
| **5432** | PostgreSQL | Internal Only | `internal_network` | **Zero host port mapping**. Only accessible to backend containers. |
| **3306** | MariaDB | Internal Only | `internal_network` | **Zero host port mapping**. Accessible only to ERPNext containers. |
| **6379** | Redis | Internal Only | `internal_network` | Password protected, internal docker network only. |
| **9092** | Redpanda / Kafka | Internal Only | `internal_network` | **Zero host port mapping**. Plaintext listener restricted to container subnet. |
| **5672** | RabbitMQ | Internal Only | `internal_network` | **Zero host port mapping**. Amqp credentials required. |
| **15672**| RabbitMQ UI | Admin Only | `127.0.0.1:15672` | Accessible via SSH Local Port Forwarding only. |

---

## 2. CORS & Cookie Policies

### Cross-Origin Resource Sharing (CORS):
- **Whitelisted Origins**:
  - `https://*.pages.dev` (Cloudflare Pages preview & production domains)
  - `https://copilot.enterprise-suite.demo`
  - `https://qc.enterprise-suite.demo`
  - `http://localhost:3000`, `http://localhost:3001` (Local development only)
- **Wildcard Disallowance**: `allow_origins=["*"]` is strictly forbidden when `allow_credentials=True`.
- **Allowed Headers**: `Authorization`, `Content-Type`, `X-Correlation-ID`, `X-Tenant-ID`.

### Cookie Security:
- `HttpOnly`: Enabled on all session cookies to prevent XSS exfiltration.
- `Secure`: Required in production (transported exclusively over HTTPS).
- `SameSite`: `Lax` for standard navigation; `Strict` for state-changing mutative operations.
- `CSRF Protection`: Double-submit cookie pattern with cryptographic HMAC token for form posts.

---

## 3. RBAC & ABAC Enforcement Model

| Role | Copilot Document Retrieval | ERP Orders (Read/Draft) | ERP Financial Posting | QC Inspection Read | QC Defect Override & Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`ANONYMOUS`** | Denied | Denied | Denied | Denied | Denied |
| **`OPERATOR`** | Public SOPs only | Read Only | Denied | View assigned jobs | Upload photo, report defect |
| **`QC_INSPECTOR`** | QC SOPs & Specs | Read Only | Denied | View all inspections | Approve, Quarantine, or Reject |
| **`MAKER` (Agent)** | Full Business RAG | Create Draft Orders | Submit for approval | View reports | Trigger QC Sync |
| **`CHECKER` (Supervisor)**| Full Business RAG | Review Draft Orders | **Approve & Post to ERP**| Review all batches | Final override & audit sign-off |
| **`SYSTEM_ADMIN`**| Full Access | Full Access | Audit & Config | Full Access | Manage models & rules |

### ABAC (Attribute-Based Access Control) Rules:
- **Tenant Isolation**: An operator can only query documents or inspect products belonging to their designated `tenant_id` and `facility_id`.
- **Value Cap Rule**: Any ERP Purchase Invoice or Sales Order with `grand_total > $10,000 USD` automatically flags an ABAC high-value attribute requiring dual Checker sign-off (Maker != Checker).

---

## 4. Container Hardening (Non-Root Execution)

All custom application Dockerfiles enforce non-root execution:
```dockerfile
# Create unprivileged system group and user
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup --no-create-home appuser

USER 1001:1001
```
Filesystem mounts for logs and temporary caches are explicitly given ownership to `uid 1001` during the multi-stage build.
