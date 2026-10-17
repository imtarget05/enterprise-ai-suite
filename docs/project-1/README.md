# PROJECT 1: Enterprise AI Copilot (CRM/ERP Assistant)

## 1. Overview
Enterprise AI Copilot is an autonomous agentic assistant built on FastAPI, LangGraph, and Qdrant Hybrid RAG. It interfaces directly with ERPNext v15 and Salesforce CRM, enforcing strict RBAC/ABAC and Human-in-the-loop (4-eyes) approvals.

## 2. Key Technical Capabilities
- **LangGraph Stateful Execution**: StateGraph with persistent checkpoints and interrupt gates on high-value orders ($> $10,000 USD).
- **Hybrid Retrieval**: BGE-M3 Dense Vector embeddings + BM25 Sparse search merged via Reciprocal Rank Fusion ($k=60$) and scored with a BGE Cross-Encoder Reranker.
- **Salesforce REST API Adapter**: OAuth 2.0 Client Credentials flow, Account & Opportunity synchronization, external ID mapping, and exponential backoff retry.
- **RabbitMQ Transactional Outbox**: Durable queues, publisher confirmations, consumer acknowledgments, and dead-letter exchange (DLQ).
- **Maker-Checker Security**: Dual-control enforcement requiring supervisor PIN `123456` before writing ledger entries.
