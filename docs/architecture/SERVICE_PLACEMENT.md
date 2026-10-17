# SERVICE PLACEMENT & TOPOLOGY MATRIX

This document specifies the exact container and service placement across the three supported profiles: `local`, `demo`, and `full`.

---

## 1. Profiles Topology Overview

```
                                  [Profiles Breakdown]
       Local Profile                     Demo Profile                      Full Profile
  +-----------------------+        +-----------------------+        +-----------------------+
  | Host Workstation      |        | Cloudflare Pages      |        | Clustered Deployment  |
  | - React Vite Dev      |        | - Frontend A & B (CDN)|        | - Distributed K8s/VMs |
  | - FastAPI A & B       |        |                       |        |                       |
  | - Embedded Mocks /    |        | Oracle A1 ARM64 VM    |        | High-Performance Nodes|
  |   Docker Services     |        | - Nginx Ingress       |        | - Clustered Redpanda  |
  | - Local MinIO         |        | - FastAPI A & B       |        | - Clustered RabbitMQ  |
  | - Local Qdrant        |        | - ERPNext + MariaDB   |        | - BGE-M3 Dense Engine |
  | - Local Redis         |        | - Postgres + Redpanda |        | - BGE Reranker Engine |
  | - SQLite / Local PG   |        | - Cloudflare R2       |        | - DeepEval CI Runner  |
  +-----------------------+        +-----------------------+        +-----------------------+
```

---

## 2. Component Placement Across Profiles

| Service / Component | Profile 1: `local` | Profile 2: `demo` | Profile 3: `full` |
| :--- | :--- | :--- | :--- |
| **Product A Frontend** | `http://localhost:3000` (Vite) | Cloudflare Pages (`https://copilot.pages.dev`) | Cloudflare Pages / Kubernetes Ingress |
| **Product B Frontend** | `http://localhost:3001` (Vite) | Cloudflare Pages (`https://qc.pages.dev`) | Cloudflare Pages / Kubernetes Ingress |
| **Product A Backend** | `localhost:8001` | Oracle A1 ARM64 (:8001 via Nginx) | Dedicated Copilot Node / Replica (:8001) |
| **Product B Backend** | `localhost:8002` | Oracle A1 ARM64 (:8002 via Nginx) | Dedicated GPU/CPU Inspection Node (:8002) |
| **Reverse Proxy** | N/A (Direct Port) | Nginx Reverse Proxy (Port 80/443) | Cloudflare Tunnel + Envoy / Nginx |
| **ERPNext v15** | Docker Compose / Local Frappe | Oracle A1 ARM64 (Port 8080 via Nginx) | Dedicated ERP Cluster |
| **MariaDB** | Docker Compose (:3306) | Oracle A1 ARM64 (Internal network only) | Clustered MariaDB Galera |
| **PostgreSQL 16** | Docker Compose (:5432) | Oracle A1 ARM64 (Internal network only) | Dedicated PostgreSQL HA Cluster |
| **Redis** | Local Redis Container (:6379) | Oracle A1 ARM64 / Upstash Free | Clustered Redis Sentinel / Cluster |
| **RabbitMQ** | Local RabbitMQ Container (:5672) | Fallback to Bounded Task Queue / Opt-in | Clustered RabbitMQ with mirrored queues |
| **Kafka / Redpanda** | Local Redpanda Container (:9092) | Single-Node Redpanda container (:9092) | 3-Node Redpanda Raft Cluster |
| **Object Storage** | Local MinIO Container (:9000) | Cloudflare R2 Cloud Object Storage | Cloudflare R2 + Multi-region S3 |
| **Vector Database** | Local Qdrant Container (:6333) | Qdrant Cloud Free Tier (1 GB) | Qdrant Distributed Enterprise |
| **LLM Tracing** | Local Mock / Langfuse Local | Langfuse Cloud Hobby Tier | Langfuse Self-Hosted / Enterprise Cloud |
| **Inference Engine** | ONNX Runtime CPU (Local Mac/PC) | ONNX Runtime CPU (ARM64 Ampere A1) | ONNX Runtime CPU + TensorRT GPU |

---

## 3. Placement Safeguards on 2 OCPU / 12GB RAM

1. **No Competing Compilations**: Docker images are pre-built via GitHub Actions multi-arch runners (`linux/arm64`) and pulled as binaries. No `pip install` with C-extension compiling is executed on the production VM.
2. **Strict Internal Isolation**: Redpanda, RabbitMQ, MariaDB, and PostgreSQL listen exclusively on internal Docker bridge networks (`172.28.0.0/16`) without publishing ports to the public host interface.
3. **Graceful Fallback**: If memory threshold exceeds 85% (10.2 GB), the telemetry agent flags non-essential telemetry and suspends background batch rerankers to keep core ERP transactions responsive.
