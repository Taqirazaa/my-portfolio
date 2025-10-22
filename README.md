# BlockGuard – Agentic AI-Driven Auditing for Blockchain Systems

## Overview
BlockGuard is a modular SaaS architecture for blockchain transaction auditing using agentic AI.

### Key Components
- Data Ingestion & Preprocessing
- CRAC Module (rule-based compliance validation)
- Multi-Model Agent Layer
  - ComplianceChecker
  - AnomalyDetector
  - RiskAssessor
  - ReportGenerator (RAG-ready)
- FastAPI backend
- PostgreSQL (metadata), FAISS (vector search)

## Local Development

### Prerequisites
- Docker + Docker Compose

### Setup
1. Copy `.env.example` to `.env` and adjust if needed.
2. Build and start services:
```bash
docker compose up --build
```

API will be at `http://localhost:8000`.

To run locally without Docker:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Endpoints
- GET `/health/` – health check
- POST `/ingest/` – ingest a list of transactions
- POST `/audit/` – run audit for provided transactions, returns `report_id`
- GET `/reports/{report_id}` – fetch generated report content

### Database schema
Tables are created on first DB connection using SQLAlchemy models in `blockguard/db/models.py`.

### Example Payload for `/ingest/` and `/audit/`
```json
[
  {
    "tx_id": "0xabc",
    "chain": "eth",
    "from_address": "0xfrom",
    "to_address": "0xto",
    "token_symbol": "USDC",
    "amount": 123.45,
    "timestamp": "2024-01-01T00:00:00Z",
    "metadata": {"note": "sample"}
  }
]
```

## Notes
- Vector store loads on demand; you can put knowledge documents under `data/knowledge_base`.
- IsolationForest used for anomaly detection; adjust `contamination` in `AnomalyDetector`.
