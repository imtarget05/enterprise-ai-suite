# 🏛️ Enterprise AI Suite: Unified Enterprise Monorepo

[![Monorepo](https://img.shields.io/badge/Architecture-1%20Monorepo%20·%202%20Products-blueviolet)](.)
[![CI Gate](https://img.shields.io/badge/CI%20Gate-100%25%20Passed-success)](.github/workflows/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev)
[![ONNX Runtime](https://img.shields.io/badge/ONNX_Runtime-CPU_ARM64-005CED)](https://onnxruntime.ai)
[![ERPNext](https://img.shields.io/badge/ERPNext-v15_Shared-0089FF)](https://erpnext.com)
[![Redpanda](https://img.shields.io/badge/Redpanda-8--Event_Stream-FF462C)](https://redpanda.com)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-Transactional_Outbox-FF6600)](https://rabbitmq.com)

> **Monorepo Cốt Lõi cho Hồ Sơ Tech Lead / Senior AI & MLOps Engineer**:
> Một GitHub Repository duy nhất (`enterprise-ai-suite`) chứa 2 sản phẩm độc lập phục vụ sản xuất, tái sử dụng hạ tầng dùng chung, nền tảng ERPNext v15 và quy trình CI/CD chuyên biệt:
> - **PROJECT 1: Enterprise AI Copilot** (Trợ lý AI Quản trị, LangGraph, Hybrid RAG, Dual-Control 4-Mắt, Salesforce REST, RabbitMQ).
> - **PROJECT 2: Visual Quality Gate** (Giám định Ngoại quan Công nghiệp, YOLOv8/ONNX CPU P50: 71ms, Redpanda 8-Event Bus, ERPNext Quality Inspection).

---

## 📌 1. Cấu Trúc Monorepo Chuẩn Hóa

```text
enterprise-ai-suite/
│
├── apps/
│   ├── enterprise-copilot/       # PROJECT 1: CRM/ERP AI Copilot
│   │   ├── frontend/             # React 18 + Vite (Cloudflare Pages)
│   │   ├── backend/              # FastAPI + LangGraph Gateway
│   │   ├── rag/                  # Qdrant + BM25 + BGE-M3 + RRF + BGE Reranker
│   │   ├── workflows/            # Stateful Graph + HITL Approvals (PIN: 123456)
│   │   ├── evaluations/          # DeepEval (Faithfulness >= 0.80, Relevancy >= 0.70)
│   │   └── tests/                # Unit & Integration Tests
│   │
│   └── visual-quality-gate/      # PROJECT 2: Visual Quality Gate
│       ├── frontend/             # React 18 Canvas Bounding Box Viewer
│       ├── backend/              # FastAPI + Industrial QC Rules Engine
│       ├── inference/            # YOLOv8 + ONNX Runtime CPU (P50: 71.2ms)
│       ├── event-consumers/      # Redpanda / Kafka 8-Event Stream Consumer
│       ├── evaluations/          # CPU Latency & Accuracy Benchmark Suite
│       └── tests/                # Inspection & Safety Isolation Tests
│
├── packages/                     # Thư viện dùng chung (Shared Packages)
│   ├── erpnext-adapter/          # Adapter ERPNext v15 chuẩn (Sales Order + Quality Inspection)
│   ├── auth-integration/        # JWT, RBAC & ABAC (Maker-Checker, Tenant Isolation)
│   ├── shared-contracts/        # Pydantic Schemas (8 QC Events, Business Events, DB Models)
│   ├── audit/                   # Tamper-Evident SHA-256 Stamp Generator
│   └── observability/           # Langfuse Cloud Tracing & OpenTelemetry Spans
│
├── integrations/
│   └── salesforce/               # Adapter REST API Salesforce (OAuth 2.0, External ID mapping)
│
├── infrastructure/
│   ├── docker/                   # Dockerfiles (Non-root UID 1001, Multi-stage) & Nginx Config
│   ├── compose/                  # Docker Compose (Local, Demo 12GB, Full Stack)
│   ├── cloudflare/               # Cloudflare Pages Headers, Redirects & CDN Edge Config
│   ├── oracle/                   # Script cấp phát OCI Always Free ARM64 (2 OCPU / 12GB RAM)
│   ├── monitoring/               # Telemetry, Rate Limiting & Diagnostics
│   └── scripts/                  # Smoke tests, Benchmark, Seeding, Backup & Restore
│
├── data/
│   ├── seed/                     # Dữ liệu tài khoản mẫu (Maker, Checker, Inspector, Admin)
│   ├── documents/                # Tài liệu SOP nghiệp vụ (Mua hàng, tồn kho, định mức)
│   └── inspection-samples/       # Metadata và dữ liệu mẫu kiểm thử ngoại quan
│
├── docs/                         # 10 Báo cáo kỹ thuật chuẩn bị kiểm toán
│   ├── project-1/                # Tài liệu thiết kế chi tiết Project 1
│   ├── project-2/                # Tài liệu thiết kế chi tiết Project 2
│   ├── architecture/             # Ma trận công nghệ, Service Placement, Network Security
│   ├── deployment/               # Kế hoạch hạ tầng 0đ, Resource Budget 12GB, Disaster Recovery
│   └── evidence/                 # Biên bản kiểm định thực tế, log benchmark ONNX CPU
│
├── .github/workflows/            # 5 Pipelines CI/CD Độc Lập
│   ├── copilot-ci.yml            # Pipeline kiểm thử Project 1 & DeepEval
│   ├── quality-gate-ci.yml       # Pipeline kiểm thử Project 2 & ONNX Benchmark
│   ├── infrastructure-ci.yml     # Kiểm tra cú pháp Compose & Nginx Ingress
│   ├── security-ci.yml           # Kiểm thử hồi quy RBAC/ABAC & Maker-Checker
│   └── deployment.yml            # Build Multi-Arch ARM64 & AMD64 Images
│
├── compose.yaml                  # Cấu hình Demo Profile (Tối ưu 12GB RAM cho Oracle Free)
├── compose.full.yaml             # Cấu hình Full Stack Profile (Redpanda + RabbitMQ + Qdrant)
├── .env.example                  # File mẫu biến môi trường
├── Makefile                      # Lệnh điều khiển 1-chạm: test, bench, smoke, up, backup
└── README.md
```

---

## 🎯 2. So Sánh & Giá Trị Kỹ Thuật Đưa Vào CV

| Góc độ Đánh giá | PROJECT 1: Enterprise AI Copilot | PROJECT 2: Visual Quality Gate |
| :--- | :--- | :--- |
| **Vai trò ứng tuyển** | **Senior AI Application / Backend Engineer** | **Senior MLOps / Computer Vision / Data Engineer** |
| **Năng lực cốt lõi** | Agentic Workflows, Advanced RAG, Enterprise Security | Edge Inference, Low-Latency CV, Event Streaming |
| **Công nghệ AI/ML** | **LangGraph** (StateGraph), **Qdrant** Hybrid RAG, BM25, BGE-M3, BGE Reranker | **YOLOv8** Quantized, **ONNX Runtime CPU** (P50: 71.2 ms), Rules Engine |
| **Tích hợp Doanh nghiệp** | **ERPNext v15** (Sales Order, Items), **Salesforce** (REST OAuth 2.0) | **ERPNext v15** (Tự động cập nhật `Quality Inspection`) |
| **Hàng đợi & Messaging**| **RabbitMQ** (Transactional Outbox, DLQ, Publisher Confirms) | **Redpanda / Kafka** (Strict 8-Event Lifecycle Stream) |
| **Tính an toàn** | Cơ chế 4-mắt: Maker $\neq$ Checker, xác thực PIN KSV (123456) | Safety Gate độc lập: LLM chỉ giải thích SOP, không quyết định hủy/nhả hàng |
| **Lưu trữ Bằng chứng** | PostgreSQL 16 (Chuỗi băm kiểm toán SHA-256) | **Cloudflare R2** / MinIO (Ảnh chụp gốc + Bounding Box) |
| **Observability & Eval**| **Langfuse Cloud** (Spans/Tokens), **DeepEval** (Faithfulness $\ge 0.8$) | Model Registry, Dataset SHA-256 Hash, Benchmark P50/P95 |

---

## 🚀 3. Hướng Dẫn Vận Hành 1-Chạm (Quickstart)

```bash
cd /Users/mainguyenbinhtan/Downloads/enterprise-ai-suite

# 1. Kích hoạt môi trường và chạy toàn bộ kiểm thử
source .venv/bin/activate
make test

# 2. Chạy benchmark suy luận ONNX CPU (Đo lường P50 / P95)
make bench

# 3. Chạy smoke test đầu cuối kiểm chứng tích hợp ERP/CRM/Queue
make smoke

# 4. Khởi chạy cụm container Demo (Tối ưu hóa 12GB RAM cho Oracle Always Free)
make up

# 5. Khởi chạy cấu hình Full Stack (Bao gồm RabbitMQ, Redpanda, Qdrant)
make up-full
```

---

## 📊 4. Nghiệm Thu 10 Cổng Chấp Thuận (Monorepo Definition of Done)

Chi tiết đầy đủ tại [`docs/evidence/FULL_STACK_VERIFICATION.md`](docs/evidence/FULL_STACK_VERIFICATION.md):

- [x] **GATE 1: Phủ Đầy Đủ Stack Trong Monorepo** — Bảng ma trận 28 công nghệ được lưu tại [`docs/architecture/STACK_COVERAGE_MATRIX.md`](docs/architecture/STACK_COVERAGE_MATRIX.md).
- [x] **GATE 2: Nghiệp Vụ ERPNext Tái Sử Dụng Thành Công** — [`packages/erpnext-adapter/`](packages/erpnext-adapter/) phục vụ đồng thời cho cả hai sản phẩm.
- [x] **GATE 3: Luồng Nghiệp Vụ Product 1 Hoạt Động Thực Tế** — Đơn hàng $12,500 USD được tạo, chặn duyệt 4-mắt, nhập PIN và ghi sổ ERP.
- [x] **GATE 4: Luồng Nghiệp Vụ Product 2 Hoạt Động Thực Tế** — Upload ảnh -> ONNX phát hiện nứt -> Safety Gate cách ly -> Đồng bộ Quality Inspection.
- [x] **GATE 5: Hạ Tầng Full Profile Chạy Được** — RabbitMQ Transactional Outbox và Redpanda 8-event streaming được kiểm thử toàn vẹn.
- [x] **GATE 6: Cấu Hình Public Frontend & API Hoàn Chỉnh** — Cloudflare Pages và Nginx reverse proxy sẵn sàng định tuyến HTTPS.
- [x] **GATE 7: Kiểm Thử An Toàn & Phân Quyền Vượt Qua** — Chặn người dùng khác tenant (ABAC), chặn Maker tự duyệt đơn hàng của mình.
- [x] **GATE 8: Chứng Minh Sao Lưu & Phục Hồi Dữ Liệu** — Script `backup.sh` và `restore.sh` đạt RTO < 15 phút.
- [x] **GATE 9: CI/CD & Smoke Test Thành Công** — 5 workflows GitHub Actions độc lập hoạt động theo từng vùng thay đổi mã nguồn.
- [x] **GATE 10: Minh Bạch Trạng Thái Thực Thi** — Phân định rõ ràng giữa hạ tầng đã deploy, kiểm thử trong CI, và sandbox cục bộ.
