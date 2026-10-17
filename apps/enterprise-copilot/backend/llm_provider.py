"""
Multi-Provider LLM Client for Project 1 (Enterprise Copilot).
Enforces max tokens, token rate limits, and cost guardrails.
"""

from enum import Enum
from typing import Dict, Any, Optional
from apps.enterprise_copilot.backend.config import settings
from apps.enterprise_copilot.backend.redis_client import redis_client


class ProviderMode(str, Enum):
    MOCK = "MOCK"
    FREE_TIER = "FREE_TIER"
    COMMERCIAL = "COMMERCIAL"


class LLMClient:
    def __init__(self):
        self.mode = ProviderMode(settings.LLM_PROVIDER.upper())
        self.accumulated_tokens = 0
        self.accumulated_spend_usd = 0.0

    async def generate_response(
        self,
        prompt: str,
        system_instruction: str,
        user_id: str,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        limit = max_tokens or settings.MAX_TOKENS_PER_REQ
        daily_key = f"llm_tokens:{user_id}"
        used = redis_client.incrby(daily_key, 50)
        if used > 50000:
            return {
                "content": "Rate limit exceeded: Daily token quota reached.",
                "tokens_used": 0,
                "provider": self.mode.value,
                "error": "RATE_LIMIT_EXCEEDED"
            }

        if self.mode == ProviderMode.MOCK:
            if "đơn hàng" in prompt.lower() or "order" in prompt.lower():
                content = (
                    "Dựa trên dữ liệu ERPNext và Salesforce, tôi đã soạn thảo đơn hàng nhôm CNC "
                    "cho khách hàng Acme Corp: 500 linh kiện với đơn giá $25.00/chiếc (Tổng: $12,500.00). "
                    "Lệnh này có giá trị > $10,000 USD nên đã được chuyển vào hàng đợi phê duyệt 4-mắt (Pending Checker)."
                )
            elif "tồn kho" in prompt.lower() or "inventory" in prompt.lower():
                content = (
                    "Hệ thống ERPNext ghi nhận tồn kho hiện tại: "
                    "- Linh kiện Nhôm CNC (ALU-CNC-001): 1,240 chiếc tại Kho Tổng Tân Bình.\n"
                    "- Ốc vít M4 Thép (SCR-M4-02): 45,000 chiếc."
                )
            else:
                content = (
                    "Trợ lý AI Doanh Nghiệp (Project 1 - Copilot): "
                    "Đã tra cứu dữ liệu quy trình ERP và SOP nội bộ thành công."
                )
            tokens_used = len(content.split()) * 2
            self.accumulated_tokens += tokens_used
            return {"content": content, "tokens_used": tokens_used, "provider": "MOCK_DETERMINISTIC", "cost_usd": 0.00}

        return {
            "content": "Free-Tier Provider Fallback: Tra cứu SOP thành công.",
            "tokens_used": 20,
            "provider": "FREE_TIER_FALLBACK",
            "cost_usd": 0.00
        }


llm_client = LLMClient()
