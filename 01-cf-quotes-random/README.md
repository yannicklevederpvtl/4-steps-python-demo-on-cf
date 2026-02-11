# Stage 1: Random Quotes (In-Memory) - Cloud Foundry Basics

A simple FastAPI application demonstrating basic Cloud Foundry deployment concepts. This stage uses in-memory data with no database or service bindings required.

## Overview

**Purpose**: Learn Cloud Foundry fundamentals
- `cf push`: Deploy applications
- `cf logs`: View application logs
- `cf routes`: Manage application routes
- `cf apps`: List applications
- Health checks: Monitor application status

**Technology Stack**:
- FastAPI: Modern Python web framework
- Python 3.11+: Runtime environment
- In-Memory Storage: No database required

## Architecture

```
┌─────────────────────────────────────┐
│      FastAPI Application            │
│  ┌───────────────────────────────┐  │
│  │  REST API Endpoints:          │  │
│  │  • GET /          - API info  │  │
│  │  • GET /quote     - Random    │  │
│  │  • GET /quotes    - All       │  │
│  │  • GET /health    - Health    │  │
│  └───────────────────────────────┘  │
└───────────────┬─────────────────────┘
                │
                ▼
        ┌───────────────┐
        │  In-Memory    │
        │  Quotes Data  │
        │  (24 quotes)  │
        └───────────────┘
```

## Prerequisites

- Cloud Foundry CLI installed
- Access to Tanzu Application Services
- No services required (in-memory only)

## Deployment

### Option 1: Python Official Buildpack (pip)

```bash
cf push -f manifest-pip.yml
```

### Option 2: UV Buildpack

```bash
cf push -f manifest-uv.yml
```

## Cloud Foundry Basics

### Deploy Application
```bash
cf push -f manifest-pip.yml
```

### View Logs
```bash
# Real-time logs
cf logs cf-quotes-random-01

# Recent logs
cf logs cf-quotes-random-01 --recent
```

### View Routes
```bash
cf routes
```

### List Applications
```bash
cf apps
```

### Health Check
Cloud Foundry automatically monitors the `/health` endpoint to ensure your application is running.

## API Endpoints

### Root Endpoint
```bash
curl https://cf-quotes-random-01.apps.your-domain.com/
```

**Response**:
```json
{
  "name": "Random Quotes Demo",
  "description": "Cloud Foundry demo with Python: In-Memory Random Quotes",
  "version": "1.0.0",
  "stage": 1,
  "features": [
    "In-memory quotes storage",
    "No database required",
    "No service bindings required"
  ],
  "endpoints": {
    "root": "/",
    "health": "/health",
    "random_quote": "/quote",
    "all_quotes": "/quotes"
  }
}
```

### Get Random Quote
```bash
curl https://cf-quotes-random-01.apps.your-domain.com/quote
```

**Response**:
```json
{
  "text": "Education is the most powerful weapon which you can use to change the world. – Nelson Mandela",
  "category": "Importance of Education"
}
```

### Get All Quotes
```bash
curl https://cf-quotes-random-01.apps.your-domain.com/quotes
```

**Response**:
```json
[
  {
    "text": "Education is the most powerful weapon which you can use to change the world. – Nelson Mandela",
    "category": "Importance of Education"
  },
  ...
]
```

### Health Check
```bash
curl https://cf-quotes-random-01.apps.your-domain.com/health
```

**Response**:
```json
{
  "status": "healthy"
}
```

## Testing

After deployment, test the endpoints:

```bash
# Get API info
curl https://YOUR-APP-URL/

# Get random quote
curl https://YOUR-APP-URL/quote

# Get all quotes
curl https://YOUR-APP-URL/quotes

# Check health
curl https://YOUR-APP-URL/health
```

## Project Structure

```
cf-quotes-random-01/
├── app.py              # FastAPI application
├── quotes.py           # In-memory quotes data
├── manifest-pip.yml    # Deployment manifest (pip)
├── manifest-uv.yml     # Deployment manifest (uv)
├── requirements.txt    # Dependencies (pip)
├── pyproject.toml      # Dependencies (uv)
├── runtime.txt         # Python version
└── README.md           # This file
```

## Next Stage

**Stage 2**: Random Quotes with PostgreSQL
- Move quotes to PostgreSQL database
- Learn `cf marketplace` and service binding
- Understand service credentials via `VCAP_SERVICES`

---

**Stage**: 1 of 4 | **Complexity**: Basic | **Services**: None
