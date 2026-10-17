"""
Configuration Management for Product A (Enterprise Copilot & Business Agent).
Reads from environment variables and manages execution profiles (local, demo, full).
"""

import os
from enum import Enum
from typing import Optional
from pydantic_settings import BaseSettings


class ExecutionProfile(str, Enum):
    LOCAL = "local"
    DEMO = "demo"
    FULL = "full"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise Copilot API"
    VERSION: str = "1.0.0"
    PROFILE: ExecutionProfile = ExecutionProfile.LOCAL
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./enterprise_copilot.db")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "false").lower() == "true"

    # Qdrant Hybrid Vector Search
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY", None)
    QDRANT_COLLECTION: str = "enterprise_knowledge"

    # ERPNext Integration
    ERPNEXT_URL: str = os.getenv("ERPNEXT_URL", "http://localhost:8080")
    ERPNEXT_API_KEY: str = os.getenv("ERPNEXT_API_KEY", "demo_erp_api_key")
    ERPNEXT_API_SECRET: str = os.getenv("ERPNEXT_API_SECRET", "demo_erp_api_secret")
    ERPNEXT_USE_SANDBOX: bool = os.getenv("ERPNEXT_USE_SANDBOX", "true").lower() == "true"

    # Salesforce Integration
    SALESFORCE_AUTH_URL: str = os.getenv("SALESFORCE_AUTH_URL", "https://login.salesforce.com/services/oauth2/token")
    SALESFORCE_INSTANCE_URL: str = os.getenv("SALESFORCE_INSTANCE_URL", "https://enterprise-demo.my.salesforce.com")
    SALESFORCE_CLIENT_ID: str = os.getenv("SALESFORCE_CLIENT_ID", "demo_sf_client_id")
    SALESFORCE_CLIENT_SECRET: str = os.getenv("SALESFORCE_CLIENT_SECRET", "demo_sf_client_secret")
    SALESFORCE_USERNAME: str = os.getenv("SALESFORCE_USERNAME", "developer@enterprise.demo")
    SALESFORCE_PASSWORD: str = os.getenv("SALESFORCE_PASSWORD", "demo_sf_password")
    SALESFORCE_USE_SANDBOX: bool = os.getenv("SALESFORCE_USE_SANDBOX", "true").lower() == "true"

    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    RABBITMQ_EXCHANGE: str = "enterprise.business.exchange"
    RABBITMQ_ENABLED: bool = os.getenv("RABBITMQ_ENABLED", "false").lower() == "true"

    # Langfuse Observability
    LANGFUSE_PUBLIC_KEY: Optional[str] = os.getenv("LANGFUSE_PUBLIC_KEY", None)
    LANGFUSE_SECRET_KEY: Optional[str] = os.getenv("LANGFUSE_SECRET_KEY", None)
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "MOCK")  # "MOCK", "FREE_TIER", "COMMERCIAL"
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    MAX_TOKENS_PER_REQ: int = 1024
    MONTHLY_BUDGET_USD: float = 0.00

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
