FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runner

WORKDIR /app

# Create unprivileged non-root user
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup --no-create-home appuser

COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appgroup packages/ /app/packages/
COPY --chown=appuser:appgroup apps/ /app/apps/

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

USER 1001:1001

EXPOSE 8001

CMD ["python", "-m", "apps.enterprise_copilot.backend.main"]
