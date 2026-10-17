.PHONY: help install test test-copilot test-qc bench smoke seed up up-full backup restore

help:
	@echo "Enterprise AI Suite Monorepo Commands:"
	@echo "  make install      - Install Python dependencies"
	@echo "  make test         - Run all unit and integration tests across monorepo"
	@echo "  make test-copilot - Run Project 1 (Copilot) tests & DeepEval"
	@echo "  make test-qc      - Run Project 2 (Visual Quality Gate) tests"
	@echo "  make bench        - Run ONNX Runtime CPU inference benchmark (P50/P95)"
	@echo "  make smoke        - Run end-to-end smoke test for both products"
	@echo "  make seed         - Seed demo users, stock items, and SOP documents"
	@echo "  make up           - Start Demo Profile containers (Bounded for Oracle 12GB)"
	@echo "  make up-full      - Start Full Profile containers (RabbitMQ, Redpanda, Qdrant)"
	@echo "  make backup       - Run automated database backup drill"
	@echo "  make restore      - Run automated restoration drill"

install:
	pip install -r requirements.txt

test:
	PYTHONPATH=. pytest -v tests/ apps/enterprise-copilot/evaluations/

test-copilot:
	PYTHONPATH=. pytest -v apps/enterprise-copilot/evaluations/ tests/test_copilot_api.py

test-qc:
	PYTHONPATH=. pytest -v tests/test_qc_api.py

bench:
	PYTHONPATH=. python apps/visual-quality-gate/evaluations/benchmark_onnx.py

smoke:
	PYTHONPATH=. python infrastructure/scripts/smoke_test.py

seed:
	PYTHONPATH=. python infrastructure/scripts/seed_demo_data.py

up:
	docker compose -f compose.yaml up -d

up-full:
	docker compose -f compose.full.yaml up -d

backup:
	bash infrastructure/scripts/backup.sh

restore:
	bash infrastructure/scripts/restore.sh
