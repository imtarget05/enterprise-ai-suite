# STACK COVERAGE & IMPLEMENTATION MATRIX (GATE 1)

This matrix defines the complete inventory of technologies, implementation status, verification status, and profile allocation across **Product A (Enterprise Copilot)** and **Product B (Visual QC & Defect Inspection)**.

---

## 1. Executive Summary & Verification Taxonomy

To maintain engineering integrity, each technology component is categorized under one of the following strict verification states:
- **IMPLEMENTED**: Fully written in production codebase with typed interfaces and zero placeholders.
- **VERIFIED LOCALLY**: Tested via unit/integration test suite against real services, embedded engines, or sandboxes on the host machine.
- **VERIFIED IN CI**: Covered by automated GitHub Actions CI/CD workflows (lint, unit tests, integration gates).
- **DEMO PROFILE**: Optimized for low-resource Always Free cloud hosting (Oracle Cloud ARM64 2 OCPU / 12GB RAM, Cloudflare Pages, Cloudflare R2, Qdrant Cloud Free, Langfuse Cloud Hobby).
- **FULL PROFILE**: Unlocks all distributed services (Self-hosted Redpanda/Kafka, RabbitMQ, BGE-M3 heavy dense embeddings, BGE reranker, DeepEval CI gates).
- **EXTERNAL REQUIREMENT**: Real production credentials (e.g. Salesforce Production Org, Oracle Cloud Tenancy) requiring explicit user provisioning before public live activation.

---

## 2. Product A — Enterprise Copilot & Business Agent

| Component / Technology | Specification Requirement | Codebase Implementation | Verification State | Profile Support |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI + Python** | Modern asynchronous REST API with Pydantic v2 schemas and OpenAPI documentation | `product-a-copilot/backend/app/main.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **ERPNext Business Integration** | Bidirectional REST API integration with ERPNext v15 (Sales Order, Purchase Invoice, Item master, Stock Ledger) | `product-a-copilot/backend/app/integrations/erpnext.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **Salesforce REST API Adapter** | OAuth 2.0 Client Credentials/JWT bearer, Account & Opportunity sync, external ID mapping, retry with exponential backoff | `product-a-copilot/backend/app/integrations/salesforce.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **LangGraph Orchestration** | StateGraph, stateful execution, persistent checkpointer, dynamic tool calling, Human-In-The-Loop interrupt | `product-a-copilot/backend/app/rag/graph.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **LlamaIndex Ingestion** | Ingestion pipeline, hierarchical document chunking, node parser, metadata extraction | `product-a-copilot/backend/app/rag/ingestion.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **Qdrant Hybrid Retrieval** | Dense vector search combined with Sparse BM25 vector payloads via Qdrant Client | `product-a-copilot/backend/app/rag/hybrid_retriever.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **Dense Embeddings (BGE-M3)** | Multi-lingual BGE-M3 embeddings (1024-dim) for high semantic fidelity | `product-a-copilot/backend/app/rag/embeddings.py` | IMPLEMENTED, VERIFIED LOCALLY | Demo (quantized/API), Full (BGE-M3) |
| **BM25 Sparse Retrieval** | Exact keyword matching, term frequency & document length normalization | `product-a-copilot/backend/app/rag/bm25.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **Reciprocal Rank Fusion (RRF)** | Rank-based fusion algorithm: $RRF(d) = \sum \frac{1}{k + r_i(d)}$ with $k=60$ | `product-a-copilot/backend/app/rag/rrf.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **BGE Reranker** | Cross-encoder cross-attention scoring for top-K candidates | `product-a-copilot/backend/app/rag/reranker.py` | IMPLEMENTED, VERIFIED LOCALLY | Demo (light), Full (BGE-reranker) |
| **RBAC / ABAC Security** | Role-Based & Attribute-Based Access Control, tenant boundaries, department filtering | `shared/auth/access_control.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **Human-In-The-Loop Approval** | Workflow pause on financial/ERP updates, Maker-Checker authorization gate | `product-a-copilot/backend/app/rag/approval.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **RabbitMQ Business Queue** | Durable exchange, transactional outbox, publisher confirm, consumer acks, dead-letter exchange (DLX) | `product-a-copilot/backend/app/integrations/rabbitmq.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Full (Demo fallback to bounded async worker) |
| **Redis Caching & State** | Session caching, semantic query cache, rate limiting, distributed lock | `product-a-copilot/backend/app/core/redis_client.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo (Upstash/local), Full |
| **PostgreSQL Application DB** | SQLAlchemy 2.0 async engine, Alembic migrations, conversation state, audit trail | `product-a-copilot/backend/app/core/db.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **Langfuse Tracing** | LLM observability, trace spans, latency, token consumption, cost attribution | `product-a-copilot/backend/app/core/telemetry.py` | IMPLEMENTED, VERIFIED LOCALLY | Local (mock), Demo (Cloud), Full |
| **DeepEval Automated Evals** | Automated tests for Faithfulness, Hallucination, and Answer Relevancy in CI | `tests/test_eval_deepeval.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Full (CI) |
| **React Frontend UI** | React 18, Vite, Tailwind CSS, real-time streaming, HITL approval dialogs | `product-a-copilot/frontend/` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |

---

## 3. Product B — Visual QC & Defect Inspection

| Component / Technology | Specification Requirement | Codebase Implementation | Verification State | Profile Support |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI + Python** | High-throughput asynchronous inspection gateway, multi-part image ingestion | `product-b-qc/backend/app/main.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **YOLOv8 Defect Detection** | Computer vision object detection for surface cracks, voids, dents, color defects | `product-b-qc/backend/app/qc/yolo_pipeline.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **ONNX Runtime CPU Inference** | Quantized ONNX model running on CPU (ARM64 & x86_64) with latency benchmarking | `product-b-qc/backend/app/qc/onnx_infer.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **Image Annotation & Review** | Bounding box coordinates normalization, confidence thresholds, visual overlays | `product-b-qc/backend/app/qc/annotation.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **Configurable QC Rules Engine** | Rule evaluation: Max Defect Area, Severity Thresholds, Auto-Quarantine, Auto-Pass | `product-b-qc/backend/app/qc/rules_engine.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **ERPNext Quality Inspection** | Automatic synchronization to ERPNext `Quality Inspection` DocType with pass/fail status | `product-b-qc/backend/app/integrations/erp_qc.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **Kafka / Redpanda 8-Event Bus** | Strict 8-event lifecycle schema: JSON schema, correlation ID, partition key, retry | `shared/events/qc_events.py` | IMPLEMENTED, VERIFIED LOCALLY | Local (Redpanda), Demo (InMemory/Redpanda), Full |
| **MinIO & Cloudflare R2 Storage** | S3-compatible object storage: local MinIO and cloud-backed Cloudflare R2 | `shared/storage/storage_manager.py` | IMPLEMENTED, VERIFIED LOCALLY | Local (MinIO), Demo (R2), Full (R2/MinIO) |
| **Deterministic vs LLM Isolation** | Safety guarantee: LLM only provides SOP explanations; deterministic rules decide quarantine | `product-b-qc/backend/app/qc/safety_gate.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **Model Versioning & Provenance** | Model registry, dataset hash, model sha256 checksum, training epoch provenance | `product-b-qc/backend/app/qc/model_registry.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **PyTorch vs ONNX Benchmark** | CPU latency benchmark suite measuring P50, P95, P99 inference and memory delta | `infra/scripts/benchmark_onnx.py` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |
| **React QC Review Frontend** | React 18, Vite, Tailwind, HTML5 Canvas annotation viewer, operator approval modal | `product-b-qc/frontend/` | IMPLEMENTED, VERIFIED LOCALLY | Local, Demo, Full |

---

## 4. Required 8 QC Event Types Specifications

All events implement the shared envelope schema (`eventId`, `correlationId`, `timestamp`, `version: "1.0"`, `partitionKey`, `retryCount`):

1. `inspection.created`: Initiated when a work order or batch triggers an inspection request.
2. `inspection.image.uploaded`: Image file stored in MinIO/R2, metadata registered with SHA-256 hash.
3. `inspection.inference.completed`: ONNX engine emits bounding boxes, defect labels, and confidence scores.
4. `inspection.review.completed`: Human QC inspector confirms, edits, or overrides automated findings.
5. `inspection.quality.decided`: Deterministic safety engine calculates verdict: `PASSED`, `REJECTED`, `QUARANTINE`.
6. `inspection.erp.sync.requested`: Outbox message queuing sync to ERPNext Quality Inspection.
7. `inspection.erp.sync.completed`: ERPNext acknowledged creation of `Quality Inspection` document.
8. `inspection.erp.sync.failed`: ERP sync failed, routed to retry queue or Dead Letter Queue (DLQ).

---

## 5. Execution Profiles Mapping

| Profile | Target Infrastructure | Resource Footprint | Message Bus | Vector / Storage | AI Inference |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Profile 1: `local`** | Local Host / Workstation | 8–16 GB RAM | Local Redpanda + Local RabbitMQ | Local Qdrant + Local MinIO | Local ONNX + Local LLM mock / provider |
| **Profile 2: `demo`** | Cloudflare Pages + Oracle Always Free ARM64 (2 OCPU / 12GB RAM) | 4–6 GB RAM Active | Lightweight bounded event engine / Redpanda Single-Node | Qdrant Cloud Free + Cloudflare R2 | Quantized ONNX CPU + External API / Provider |
| **Profile 3: `full`** | Distributed / Dedicated Cluster | 16–32 GB RAM | Clustered Redpanda + Clustered RabbitMQ | Distributed Qdrant + Multi-bucket R2/MinIO | BGE-M3 Dense + BGE Reranker + DeepEval Evals |

---

## 6. Acceptance Gate 1 Sign-Off

- [x] All 28 required stack items explicitly mapped to concrete files in this repository.
- [x] Clear division between deterministic inspection rules and LLM advisory tasks.
- [x] All 8 required QC event types formalized with schemas and partition strategies.
- [x] Sizing bounds documented for Oracle Always Free (2 OCPU / 12GB RAM).
