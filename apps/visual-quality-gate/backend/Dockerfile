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
COPY --chown=appuser:appgroup shared/ /app/shared/
COPY --chown=appuser:appgroup product-b-qc/backend/ /app/product-b-qc/backend/

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV OMP_NUM_THREADS=2
ENV intra_op_num_threads=2

USER 1001:1001

EXPOSE 8002

CMD ["python", "product-b-qc/backend/app/main.py"]
