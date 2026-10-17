"""
Modal Cloud Serverless Deployment for Project 1 (Enterprise Copilot API).
Deploys FastAPI backend to serverless cloud containers with automatic HTTPS,
connecting to Neon Cloud PostgreSQL and Cloudflare Edge.
"""

import modal

app = modal.App("enterprise-copilot-api")

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
        "psycopg[binary]>=3.1.0",
    )
    .add_local_dir("packages", remote_path="/root/packages")
    .add_local_dir("apps/enterprise-copilot", remote_path="/root/apps/enterprise-copilot")
    .add_local_dir("integrations", remote_path="/root/integrations")
    .run_commands(
        "mkdir -p /root/apps",
        "ln -sf /root/apps/enterprise-copilot /root/apps/enterprise_copilot",
        "ln -sf /root/packages/auth-integration /root/packages/auth_integration",
        "ln -sf /root/packages/shared-contracts /root/packages/shared_contracts",
        "ln -sf /root/packages/erpnext-adapter /root/packages/erpnext_adapter",
    )
    .env({
        "PYTHONPATH": "/root",
        "DATABASE_URL": "postgresql://neondb_owner:npg_5XzkMLSBjH4m@ep-autumn-sky-b35l6g69-pooler.c-4.ap-southeast-1.aws.neon.tech/neondb?sslmode=require",
        "PROFILE": "demo",
        "ERPNEXT_USE_SANDBOX": "true",
        "SALESFORCE_USE_SANDBOX": "true",
        "LLM_PROVIDER": "FREE_TIER",
    })
)


@app.function(image=image, scaledown_window=300)
@modal.asgi_app()
def fastapi_app():
    import sys
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")
    from apps.enterprise_copilot.backend.main import app as web_app
    return web_app
