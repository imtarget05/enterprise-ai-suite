# Sổ tay Vận hành & Triển khai Production (Production Runbook)
## Hướng dẫn Triển khai Hệ thống Doanh nghiệp Chi phí 0đ (Zero-Cost Free Tier)

Tài liệu này hướng dẫn chi tiết từng bước đưa hệ sinh thái **Enterprise AI Suite** (Project 1 & Project 2) lên môi trường Internet công khai, hoàn toàn sử dụng các gói hạ tầng miễn phí vĩnh viễn (Always Free).

---

## 1. Bản đồ Hạ tầng Triển khai (Infrastructure Map)

```
                            [ Internet Users ]
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
       ┌────────────────────────┐      ┌────────────────────────┐
       │    Cloudflare Pages    │      │    Cloudflare Pages    │
       │  (Enterprise Copilot)  │      │ (Visual Quality Gate)  │
       │    https://copilot.*   │      │      https://qc.*      │
       └────────────┬───────────┘      └────────────┬───────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │ (HTTPS Reverse Proxy)
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │   Oracle Cloud Always Free ARM64 VM (2 OCPU / 12GB)    │
       │                                                        │
       │  ┌──────────────────────────────────────────────────┐  │
       │  │               Nginx Gateway (:80/:443)           │  │
       │  └──────────┬────────────────────────────┬──────────┘  │
       │             ▼                            ▼             │
       │   ┌──────────────────┐         ┌──────────────────┐    │
       │   │ Copilot API :8001│         │  QC API :8002    │    │
       │   │  (LangGraph RAG) │         │  (ONNX Runtime)  │    │
       │   └─────────┬────────┘         └─────────┬────────┘    │
       │             │                            │             │
       │             ▼                            ▼             │
       │   ┌───────────────────────────────────────────────┐    │
       │   │   PostgreSQL 16 + Redis 7 + Swapfile 4GB      │    │
       │   └───────────────────────────────────────────────┘    │
       └────────────────────────────────────────────────────────┘
```

---

## 2. Bước 1: Triển khai Frontend lên Cloudflare Pages

Cả 2 frontend React đều được đóng gói độc lập và triển khai trực tiếp từ Monorepo GitHub:

### A. Project 1 — Enterprise Copilot Frontend
1. Đăng nhập [Cloudflare Dashboard](https://dash.cloudflare.com/) $\rightarrow$ **Workers & Pages** $\rightarrow$ **Create application** $\rightarrow$ **Pages** $\rightarrow$ **Connect to Git**.
2. Chọn repository: `enterprise-ai-suite`.
3. Cấu hình Build Settings:
   - **Project Name**: `enterprise-copilot`
   - **Framework preset**: `Vite`
   - **Root directory**: `apps/enterprise-copilot/frontend`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
4. Cấu hình Environment Variables:
   - `VITE_API_BASE_URL`: `https://api.yourdomain.com/api/copilot`
5. Nhấn **Save and Deploy**. Cloudflare Pages sẽ tự động kích hoạt HTTPS và gắn domain miễn phí `*.pages.dev`.

### B. Project 2 — Visual Quality Gate Frontend
1. Chọn **Create application** $\rightarrow$ **Pages** $\rightarrow$ **Connect to Git**.
2. Chọn repository: `enterprise-ai-suite`.
3. Cấu hình Build Settings:
   - **Project Name**: `enterprise-visual-qc`
   - **Framework preset**: `Vite`
   - **Root directory**: `apps/visual-quality-gate/frontend`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
4. Cấu hình Environment Variables:
   - `VITE_QC_API_BASE_URL`: `https://api.yourdomain.com/api/qc`
5. Nhấn **Save and Deploy**.

---

## 3. Bước 2: Triển khai Backend lên Oracle Cloud Always Free VM

### A. Khởi tạo VM ARM64
1. Truy cập [Oracle Cloud Console](https://cloud.oracle.com/).
2. Tạo Compute Instance:
   - **Image**: Ubuntu 22.04 LTS (Canonical Ubuntu Server).
   - **Shape**: `VM.Standard.A1.Flex` (Ampere ARM64) với **2 OCPU** và **12 GB RAM**.
   - **Boot Volume**: 50 GB.
   - Thêm SSH Public Key của bạn.
3. Trong Virtual Cloud Network (VCN) Ingress Rules, mở cổng `22`, `80`, `443`.

### B. Chạy Script Thiết lập Tự động
SSH vào VM:
```bash
ssh -i ~/.ssh/id_rsa ubuntu@<YOUR_VM_PUBLIC_IP>
```
Clone repo và chạy provisioning script:
```bash
git clone https://github.com/your-org/enterprise-ai-suite.git
cd enterprise-ai-suite

# Cấp quyền và chạy script chuẩn bị VM (cài Docker, UFW, Swapfile 4GB)
chmod +x infrastructure/oracle/provision_oci_vm.sh
bash infrastructure/oracle/provision_oci_vm.sh
```

### C. Cấu hình Môi trường `.env`
Sao chép mẫu và cập nhật các biến môi trường:
```bash
cp .env.example .env
nano .env
```
Các tham số quan trọng:
```ini
PROFILE=demo
DATABASE_URL=postgresql://postgres:enterprise_secure_pg_pass_2026@postgres-core:5432/enterprise_suite
REDIS_ENABLED=true
LLM_PROVIDER=FREE_TIER
GEMINI_API_KEY=<YOUR_GOOGLE_AI_STUDIO_API_KEY>
STORAGE_PROVIDER=r2
STORAGE_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
STORAGE_ACCESS_KEY=<YOUR_R2_ACCESS_KEY>
STORAGE_SECRET_KEY=<YOUR_R2_SECRET_KEY>
```

### D. Khởi chạy Dịch vụ Docker
```bash
# Khởi chạy toàn bộ hệ thống bằng Docker Compose (Bounded cho 12GB RAM)
docker compose -f compose.yaml up -d --build
```
Kiểm tra trạng thái container:
```bash
docker compose -f compose.yaml ps
```

---

## 4. Bước 3: Cấu hình Tên miền & Chứng chỉ HTTPS

1. Thêm bản ghi DNS trên Cloudflare:
   - `A api.yourdomain.com` $\rightarrow$ `<YOUR_VM_PUBLIC_IP>` (Proxy status: **Proxied**).
2. Cloudflare tự động xử lý chứng chỉ SSL/TLS miễn phí (Universal SSL).
3. Đảm bảo chế độ SSL/TLS trong Cloudflare đặt là **Full** hoặc **Full (strict)**.

---

## 5. Bước 4: Kiểm tra & Xác nhận Triển khai

Chạy công cụ kiểm định tự động từ máy local hoặc ngay trên server:
```bash
# 1. Kiểm tra toàn bộ endpoint công khai
python infrastructure/scripts/verify_public_endpoints.py --base-url https://api.yourdomain.com

# 2. Chạy kịch bản tự động hóa kiểm tra toàn diện
bash infrastructure/scripts/deploy_production.sh
```

---

## 6. Sổ tay Xử lý Sự cố (Troubleshooting Runbook)

| Hiện tượng | Nguyên nhân có thể | Cách khắc phục |
| :--- | :--- | :--- |
| **502 Bad Gateway** | FastAPI service đang khởi động hoặc crash | Chạy `docker logs copilot-api-prod` hoặc `docker logs qc-api-prod` để xem traceback |
| **Out of Memory (OOM)** | Vượt hạn mức 12GB RAM | Kiểm tra swapfile: `free -m`. Đảm bảo không bật Profile `full` cùng lúc với quá nhiều container nặng |
| **CORS Error trên Frontend** | Sai cấu hình header trong Nginx | Kiểm tra file `infrastructure/docker/nginx.conf` và kiểm tra biến `VITE_API_BASE_URL` |
| **Rate Limit LLM** | Vượt hạn mức 15 RPM của Gemini Free | Hệ thống sẽ tự động fallback về deterministic response mà không gây lỗi giao dịch |
