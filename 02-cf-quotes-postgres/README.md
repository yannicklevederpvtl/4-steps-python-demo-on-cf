# Stage 2: Random Quotes with PostgreSQL - Service Marketplace & Binding

A FastAPI application demonstrating Cloud Foundry service marketplace and binding concepts. This stage uses PostgreSQL database for quote storage, requiring service binding.

## Overview

**Purpose**: Learn Cloud Foundry service marketplace and binding
- `cf marketplace`: Browse available services
- `cf create-service`: Create service instances
- `cf bind-service`: Bind services to applications
- `VCAP_SERVICES`: Access service credentials
- Service discovery: Automatic credential injection

**Technology Stack**:
- FastAPI: Modern Python web framework
- PostgreSQL: Database for quote storage
- Python 3.11+: Runtime environment
- Service Binding: Cloud Foundry service integration

## Architecture

```
┌─────────────────────────────────────┐
│      FastAPI Application            │
│  ┌───────────────────────────────┐  │
│  │  REST API Endpoints:          │  │
│  │  • GET /          - API info  │  │
│  │  • GET /quote     - Random    │  │
│  │  • GET /quotes    - All       │  │
│  │  • POST /quotes/init - Load   │  │
│  │  • POST /quotes/clean - Reset │  │
│  │  • GET /health    - Health    │  │
│  └───────────────────────────────┘  │
└───────────────┬─────────────────────┘
                │
                ▼
        ┌───────────────┐
        │  PostgreSQL   │
        │  Database     │
        │  (vector-db)  │
        └───────────────┘
```

## Prerequisites

- Cloud Foundry CLI installed
- Access to Tanzu Application Services
- PostgreSQL service available in marketplace

## Service Marketplace

### Browse Available Services
```bash
cf marketplace
```

### Create PostgreSQL Service Instance
```bash
# Find PostgreSQL service name and plan
cf marketplace

# Create service instance (example)
cf create-service <postgres-service> <plan> vector-db
```

### Verify Service Instance
```bash
cf services
```

## Deployment

### Option 1: Python Official Buildpack (pip)

```bash
cf push -f manifest-pip.yml
```

### Option 2: UV Buildpack

```bash
cf push -f manifest-uv.yml
```

**Note**: The service binding is configured in the manifest. The service instance (`vector-db`) must exist before deployment.

## Service Binding

### Automatic Binding (via Manifest)
The manifest includes the service binding:
```yaml
services:
  - vector-db
```

### Manual Binding
```bash
cf bind-service cf-quotes-postgres-02 vector-db
cf restage cf-quotes-postgres-02
```

### Verify Service Binding
```bash
# Check bound services
cf services

# View service credentials (in app)
cf env cf-quotes-postgres-02
```

## API Endpoints

### Root Endpoint
```bash
curl https://cf-quotes-postgres-02.apps.your-domain.com/
```

**Response**:
```json
{
  "name": "Random Quotes Demo - Stage 2",
  "description": "Cloud Foundry demo with Python: Random Quotes with PostgreSQL",
  "version": "1.0.0",
  "stage": 2,
  "features": [
    "PostgreSQL database storage",
    "Cloud Foundry service binding",
    "Service marketplace integration"
  ],
  "endpoints": {
    "root": "/",
    "health": "/health",
    "random_quote": "/quote",
    "all_quotes": "/quotes",
    "init_quotes": "POST /quotes/init",
    "clean_quotes": "POST /quotes/clean"
  }
}
```

### Get Random Quote
```bash
curl https://cf-quotes-postgres-02.apps.your-domain.com/quote
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
curl https://cf-quotes-postgres-02.apps.your-domain.com/quotes
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

### Initialize Quotes
```bash
curl -X POST https://cf-quotes-postgres-02.apps.your-domain.com/quotes/init
```

**Response**:
```json
{
  "status": "success",
  "message": "Quotes loaded successfully",
  "count": 24
}
```

### Clean Database
```bash
curl -X POST https://cf-quotes-postgres-02.apps.your-domain.com/quotes/clean
```

**Response**:
```json
{
  "status": "success",
  "message": "Database cleaned"
}
```

### Health Check
```bash
curl https://cf-quotes-postgres-02.apps.your-domain.com/health
```

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "database": "ok"
  }
}
```

## Testing

After deployment, test the endpoints:

```bash
# Get API info
curl https://YOUR-APP-URL/

# Initialize quotes (required before using /quote)
curl -X POST https://YOUR-APP-URL/quotes/init

# Get random quote
curl https://YOUR-APP-URL/quote

# Get all quotes
curl https://YOUR-APP-URL/quotes

# Check health
curl https://YOUR-APP-URL/health

# Clean database
curl -X POST https://YOUR-APP-URL/quotes/clean
```

## Project Structure

```
cf-quotes-postgres-02/
├── app.py              # FastAPI application
├── quotes.py           # Quotes data + database functions
├── database.py         # PostgreSQL integration
├── utils/        # Service binding utilities
│   ├── __init__.py
│   └── cfpostgres.py   # PostgreSQL service discovery
├── manifest-pip.yml    # Deployment manifest (pip)
├── manifest-uv.yml     # Deployment manifest (uv)
├── requirements.txt    # Dependencies (pip)
├── pyproject.toml      # Dependencies (uv)
├── runtime.txt         # Python version
└── README.md           # This file
```

## Previous Stage

**Stage 1**: Random Quotes (In-Memory)
- Basic Cloud Foundry deployment
- In-memory data storage
- No service bindings required

## Next Stage

**Stage 3**: Semantic Quotes with PostgreSQL
- Add vector similarity search
- Introduce AI embedding models
- Learn semantic search capabilities

---

**Stage**: 2 of 4 | **Complexity**: Intermediate | **Services**: PostgreSQL
