# Stage 3: Semantic Quotes with PostgreSQL - AI Services & Vector Search

A FastAPI application demonstrating AI embedding services and vector similarity search. This stage uses PostgreSQL with pgvector for semantic search, requiring both embedding and database service bindings.

## Overview

**Purpose**: Learn AI services and vector similarity search
- AI embedding models: Generate vector representations of text
- Vector databases: Store and search embeddings efficiently
- Semantic search: Find quotes by meaning, not just keywords
- Cosine similarity: Measure semantic similarity between vectors
- Service integration: Multiple service bindings working together

**Technology Stack**:
- FastAPI: Modern Python web framework
- PostgreSQL + pgvector: Vector database for similarity search
- AI Embedding Service: Generate text embeddings
- LangChain: Framework for LLM applications
- Python 3.11+: Runtime environment

## Architecture

```
┌─────────────────────────────────────┐
│      FastAPI Application            │
│  ┌───────────────────────────────┐  │
│  │  REST API Endpoints:          │  │
│  │  • GET /          - API info  │  │
│  │  • GET /quotes?topic=<query>  │  │
│  │  • POST /quotes/init - Load   │  │
│  │  • POST /quotes/clean - Reset │  │
│  │  • GET /words    - Compare    │  │
│  │  • GET /health    - Health    │  │
│  └───────────────────────────────┘  │
└───────────────┬─────────────────────┘
                │
        ┌───────┴───────┐
        │               │
        ▼               ▼
┌───────────────┐  ┌──────────────┐
│   Embedding   │  │  PostgreSQL  │
│   Service     │  │  + pgvector  │
│               │  │              │
│ tanzu-nomic-  │  │ vector-db    │
│ embed-text    │  │              │
│               │  │ • Vector     │
│ • Generate    │  │   Storage    │
│   Embeddings  │  │ • Similarity │
│               │  │   Search     │
└───────────────┘  └──────────────┘
```

## Prerequisites

- Cloud Foundry CLI installed
- Access to Tanzu Application Services
- PostgreSQL service with pgvector (vector-db)
- AI embedding service (tanzu-nomic-embed-text)

## Service Setup

### Create Service Instances
```bash
# Create PostgreSQL service
cf create-service <postgres-service> <plan> vector-db

# Create embedding service
cf create-service <embedding-service> <plan> tanzu-nomic-embed-text
```

### Verify Services
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

**Note**: Both services must be bound before deployment. The manifest includes both service bindings.

## API Endpoints

### Root Endpoint
```bash
curl https://cf-quotes-semantic-03.apps.your-domain.com/
```

**Response**:
```json
{
  "name": "Semantic Quotes Demo - Stage 3",
  "description": "Cloud Foundry demo with Python: Semantic Quotes with PostgreSQL",
  "version": "1.0.0",
  "stage": 3,
  "features": [
    "Vector similarity search",
    "AI embedding models",
    "PostgreSQL with pgvector",
    "Semantic search capabilities"
  ],
  "endpoints": {
    "root": "/",
    "health": "/health",
    "quotes": "/quotes?topic=<query>",
    "words": "/words",
    "init": "POST /quotes/init",
    "clean": "POST /quotes/clean"
  }
}
```

### Semantic Search
```bash
curl "https://cf-quotes-semantic-03.apps.your-domain.com/quotes?topic=education"
```

**Response**:
```json
[
  {
    "text": "Education is the most powerful weapon which you can use to change the world. – Nelson Mandela",
    "similarity": 0.85,
    "category": "Importance of Education"
  },
  ...
]
```

### Get All Quotes (No Topic)
```bash
curl https://cf-quotes-semantic-03.apps.your-domain.com/quotes
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
curl -X POST https://cf-quotes-semantic-03.apps.your-domain.com/quotes/init
```

**Response**:
```json
{
  "status": "success",
  "message": "Quotes loaded successfully",
  "count": 24
}
```

### Word Similarity
```bash
curl "https://cf-quotes-semantic-03.apps.your-domain.com/words?word1=education&word2=learning"
```

**Response**:
```json
[
  {
    "word1": "education",
    "word2": "learning",
    "similarity": 0.78
  }
]
```

### Health Check
```bash
curl https://cf-quotes-semantic-03.apps.your-domain.com/health
```

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "embedding": "ok",
    "database": "ok",
    "vectorstore": "initialized",
    "embeddings": "initialized"
  }
}
```

## Testing

After deployment, test the endpoints:

```bash
# Get API info
curl https://YOUR-APP-URL/

# Initialize quotes (required before search)
curl -X POST https://YOUR-APP-URL/quotes/init

# Semantic search
curl "https://YOUR-APP-URL/quotes?topic=hard work"

# Word similarity
curl "https://YOUR-APP-URL/words?word1=success&word2=achievement"

# Check health
curl https://YOUR-APP-URL/health

# Clean database
curl -X POST https://YOUR-APP-URL/quotes/clean
```

## Project Structure

```
cf-quotes-semantic-03/
├── app.py              # FastAPI application
├── quotes.py           # Quotes data + vector loading
├── embeddings.py       # Custom embeddings wrapper
├── vector_store.py     # PGVector initialization
├── similarity.py       # Similarity search logic
├── utils/        # Service binding utilities
│   ├── __init__.py
│   ├── cfgenai.py      # AI service discovery
│   └── cfpostgres.py   # Database service discovery
├── manifest-pip.yml    # Deployment manifest (pip)
├── manifest-uv.yml     # Deployment manifest (uv)
├── requirements.txt    # Dependencies (pip)
├── pyproject.toml      # Dependencies (uv)
├── runtime.txt         # Python version
└── README.md           # This file
```

## Previous Stage

**Stage 2**: Random Quotes with PostgreSQL
- PostgreSQL database storage
- Service marketplace and binding
- Basic database operations

## Next Stage

**Stage 4**: Semantic Quotes MCP
- Transform into MCP server
- HTTP/SSE streaming support
- MCP protocol compliance

---

**Stage**: 3 of 4 | **Complexity**: Advanced | **Services**: PostgreSQL + AI Embedding
