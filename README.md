# Portal Transaction Monitor

A Python automation platform that monitors business registry portals for data anomalies — built to demonstrate production-grade automation engineering.

## What it does

Simulates an enterprise automation platform that:

- **Scrapes** business registry portals via Playwright browser automation
- **Verifies** scraped data against an authoritative API source
- **Detects anomalies** when portal data diverges from API data
- **Retries automatically** on failure (up to 3 attempts with 30s delay)
- **Monitors continuously** via scheduled Celery Beat tasks (every 10 minutes)
- **Tracks everything** — every transaction stored in PostgreSQL with full audit trail

## Architecture

```
Celery Beat (scheduler)
       ↓
Celery Worker
       ↓
  ┌─────────────┐     ┌─────────────┐
  │   Scraper   │     │   Verifier  │
  │ (Playwright)│     │    (API)    │
  └─────────────┘     └─────────────┘
         ↓                   ↓
         └────────┬──────────┘
                  ↓
            ┌──────────┐
            │PostgreSQL│
            └──────────┘
                  ↑
            ┌──────────┐
            │ FastAPI  │
            └──────────┘
```

## Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Web framework | FastAPI |
| Browser automation | Playwright + playwright-stealth |
| Task queue | Celery + Celery Beat |
| Message broker | Redis |
| Database | PostgreSQL + SQLAlchemy (async) |
| Containerization | Docker Compose |

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

API available at `http://localhost:8000/docs`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/transactions` | List transactions with optional status filter |
| GET | `/transactions/stats` | Success rate and counts by status |
| POST | `/transactions/run` | Manually trigger monitoring for a company |

### Example — trigger monitoring

```bash
curl -X POST "http://localhost:8000/transactions/run?company_number=00445790&jurisdiction_code=gb"
```

### Example — get stats

```bash
curl http://localhost:8000/transactions/stats
```

```json
{
  "total_transactions": 30,
  "success_rate": "93.33%",
  "by_status": {
    "SUCCESS": 28,
    "ANOMALY": 1,
    "FAILED": 1,
    "RETRY": 0
  }
}
```

## Transaction statuses

| Status | Description |
|--------|-------------|
| `SUCCESS` | Portal and API data match |
| `ANOMALY` | Data mismatch detected between portal and API |
| `FAILED` | All retry attempts exhausted |
| `RETRY` | Task queued for retry after failure |

## Anomaly detection

When portal data diverges from API data, the transaction is flagged as `ANOMALY` with full details:

```json
{
  "status": "ANOMALY",
  "anomalies": {
    "status": {
      "web": "Active",
      "api": "Dissolved"
    }
  }
}
```

Fields compared on every transaction: `name`, `status`, `incorporation_date`.

## Retry logic

Failed tasks are automatically retried up to 3 times with a 30-second delay between attempts. This handles transient portal failures without generating false `FAILED` records.

## Mock portal

This project uses a local mock portal (port 8001) that mimics the HTML structure of a real business registry. In production, Playwright would target actual enterprise portals — the scraping logic, retry handling, and anomaly detection remain identical.

The mock allows full local testing without dependency on external services or bot detection systems. Real portals typically require authenticated sessions and residential proxies to bypass anti-bot protection.

## Project structure

```
portal-transaction-monitor/
├── app/
│   ├── scraper/            # Playwright browser automation
│   ├── verifier/           # API cross-verification and anomaly detection
│   ├── tasks/              # Celery tasks and Beat schedule
│   ├── api/                # FastAPI endpoints
│   ├── models/             # SQLAlchemy models
│   ├── mock_portal/        # Local portal simulator
│   └── config.py           # Settings from environment
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```
