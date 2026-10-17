# LLM COST GUARDRAILS & RESOURCE SPENDING LIMITS

This policy enforces strict technical guardrails to prevent unbudgeted cloud expenditures, API overages, and token exhaustion across all runtime environments.

---

## 1. Provider Adapter Hierarchy

The AI engine integrates an abstracted LLM Client (`product-a-copilot/backend/app/core/llm_provider.py`) operating under three explicit modes:

1. **`ProviderMode.MOCK` (Default for Offline / CI Tests)**:
   - Emits deterministic, synthetic responses based on golden evaluation datasets.
   - Cost: **$0.00**. Zero network calls to external APIs.
   - Used in automated unit testing, CI pipelines, and local development without keys.
2. **`ProviderMode.FREE_TIER` (Demo Profile)**:
   - Connects to genuinely free provider quotas (e.g. Google Gemini API free tier / Cloudflare Workers AI free allowance / local ONNX / quantized CPU LLM).
   - Bounded by strict rate limits (15 requests/minute).
3. **`ProviderMode.COMMERCIAL` (Explicit Opt-In Only)**:
   - Connects to OpenAI, Anthropic, or Azure OpenAI only when credentials and a non-zero spending limit are explicitly supplied in `.env`.

---

## 2. Hard Spending Limits & Token Controls

| Control Parameter | Default Value | Enforcement Mechanism | Failure Action |
| :--- | :--- | :--- | :--- |
| **Max Tokens per Request** | 1,024 tokens | FastAPI Request Validator | Truncates prompt or rejects with HTTP 400 |
| **Request Timeout** | 15.0 seconds | Asyncio Timeout Context | Cancels request, logs timeout, falls back to SOP cache |
| **Per-User Daily Budget** | 20,000 tokens (~$0.04) | Redis Sliding Window Counter | Returns HTTP 429 "Daily token quota exceeded" |
| **Global Monthly Spend Cap** | $0.00 (Demo) / $25.00 (Prod)| Persistent DB Ledger Check | Hard trip-switch: disables commercial LLM; switches to Mock/Cache |
| **Concurrent LLM Calls** | 4 parallel requests | Asyncio Bounded Semaphore | Queues up to 10 requests, rejects excess with HTTP 503 |

---

## 3. Rate Limiting Algorithm (Redis Token Bucket)

```python
# Conceptual implementation in shared rate limiter
async def check_rate_limit(user_id: str, estimated_tokens: int) -> bool:
    key = f"rate_limit:{user_id}:{datetime.date.today().isoformat()}"
    current_usage = await redis.incrby(key, estimated_tokens)
    if current_usage == estimated_tokens:
        await redis.expire(key, 86400) # 24 hour TTL
    return current_usage <= USER_DAILY_TOKEN_LIMIT
```

---

## 4. Admin Diagnostics & Usage Reporting

The admin diagnostics endpoint (`GET /api/copilot/v1/diagnostics/cost`) returns real-time telemetry:
```json
{
  "active_provider": "FREE_TIER_GEMINI_FALLBACK",
  "monthly_budget_usd": 0.00,
  "accumulated_spend_usd": 0.00,
  "tokens_consumed_month": 48210,
  "cache_hit_ratio": 0.68,
  "circuit_breaker_status": "CLOSED",
  "mock_mode_available": true
}
```
If accumulated spend reaches 90% of budget, alert webhooks trigger to administrator email and logging sinks.
