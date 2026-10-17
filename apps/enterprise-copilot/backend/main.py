"""
FastAPI Main Application Entrypoint for Project 1 (Enterprise Copilot).
Configures CORS, life-span hooks, health endpoints, and router bindings.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.enterprise_copilot.backend.routes import router as copilot_router
from apps.enterprise_copilot.backend.config import settings
from apps.enterprise_copilot.backend.db import init_db
from apps.enterprise_copilot.backend.rabbitmq import rabbitmq_broker
from apps.enterprise_copilot.rag.hybrid_retriever import hybrid_retriever


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    sample_docs = [
        {
            "id": "SOP-PROC-01",
            "title": "Quy trình Mua hàng & Duyệt Đơn hàng",
            "content": "Theo quy định quản trị tài chính doanh nghiệp: Đơn hàng linh kiện nhôm CNC "
                       "có giá trị vượt 10,000 USD bắt buộc phải qua phê duyệt 4-mắt từ Kiểm soát viên (Checker) "
                       "và xác thực mã PIN bảo mật. Đơn giá nhôm CNC mã ALU-CNC-001 chuẩn là $25.00/chiếc.",
        },
        {
            "id": "SOP-INV-02",
            "title": "Quy định Quản lý Tồn kho Vật tư",
            "content": "Tồn kho an toàn tối thiểu cho linh kiện nhôm ALU-CNC-001 là 500 chiếc. "
                       "Nếu tồn kho khả dụng dưới định mức, hệ thống phải tự động tạo phiếu đề xuất mua hàng (Purchase Requisition).",
        },
    ]
    hybrid_retriever.index_documents(sample_docs)
    if settings.RABBITMQ_ENABLED:
        await rabbitmq_broker.connect()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://enterprise-copilot.pages.dev",
        "https://enterprise-qc.pages.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(copilot_router, prefix="/api/copilot")


@app.get("/api/copilot/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "Project 1 - Enterprise Copilot",
        "version": settings.VERSION,
        "profile": settings.PROFILE.value,
        "qdrant_configured": bool(settings.QDRANT_URL),
        "erpnext_sandbox": settings.ERPNEXT_USE_SANDBOX,
        "salesforce_sandbox": settings.SALESFORCE_USE_SANDBOX,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.enterprise_copilot.backend.main:app", host="0.0.0.0", port=8001, reload=True)
