"""
Modal Cloud Serverless Deployment for Project 2 (Visual Quality Gate API).
Deploys FastAPI backend + ONNX Runtime CPU detector to serverless cloud containers,
connecting to Neon Cloud PostgreSQL and Cloudflare Edge.
"""

import modal

app = modal.App("visual-qc-api")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi>=0.115.0",
        "uvicorn>=0.30.0",
        "pydantic>=2.8.0",
        "pydantic-settings>=2.4.0",
        "sqlalchemy>=2.0.30",
        "httpx>=0.27.0",
        "PyJWT>=2.8.0",
        "python-multipart>=0.0.9",
        "numpy>=1.26.0",
        "onnxruntime>=1.18.0",
        "pillow>=10.0.0",
        "psycopg[binary]>=3.1.0",
    )
    .add_local_dir("packages", remote_path="/root/packages")
    .add_local_dir("apps/visual-quality-gate", remote_path="/root/apps/visual-quality-gate")
    .add_local_dir("models", remote_path="/root/models")
    .run_commands(
        "mkdir -p /root/apps",
        "ln -sf /root/apps/visual-quality-gate /root/apps/visual_quality_gate",
        "ln -sf /root/apps/visual-quality-gate/event-consumers /root/apps/visual-quality-gate/event_consumers",
        "ln -sf /root/packages/auth-integration /root/packages/auth_integration",
        "ln -sf /root/packages/shared-contracts /root/packages/shared_contracts",
        "ln -sf /root/packages/erpnext-adapter /root/packages/erpnext_adapter",
    )
    .env({
        "PYTHONPATH": "/root",
        "DATABASE_URL": "postgresql://neondb_owner:npg_5XzkMLSBjH4m@ep-autumn-sky-b35l6g69-pooler.c-4.ap-southeast-1.aws.neon.tech/neondb?sslmode=require",
        "PROFILE": "demo",
        "ERPNEXT_USE_SANDBOX": "true",
        "ONNX_MODEL_PATH": "/root/models/defect_yolov8n_quantized.onnx",
        "INFERENCE_THREADS": "2",
        "OMP_NUM_THREADS": "2",
        "intra_op_num_threads": "2",
    })
)


@app.function(image=image, scaledown_window=300)
@modal.asgi_app()
def fastapi_app():
    import sys
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")
    from apps.visual_quality_gate.backend.main import app as web_app
    return web_app
