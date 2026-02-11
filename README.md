# Cloud Foundry Python Quotes Demo - Progressive Workshop

A progressive workshop demonstrating Cloud Foundry deployment concepts through four stages of increasing complexity, from basic in-memory applications to advanced semantic search and MCP integration.

## Overview

This repository contains four progressive stages of a quotes application, each building upon the previous stage to introduce new Cloud Foundry concepts:

1. **Stage 1: Random Quotes (In-Memory)** - Basic Cloud Foundry deployment
2. **Stage 2: Random Quotes with PostgreSQL** - Service marketplace and binding
3. **Stage 3: Semantic Quotes Search** - Vector embeddings and semantic search
4. **Stage 4: MCP Integration** - Model Context Protocol integration

## Prerequisites

- Cloud Foundry CLI installed and configured
- Access to Tanzu Application Services (TAS) platform
- Python 3.11+ (for local development)
- `uv` package manager (recommended) or `pip`

## Service Configuration

**Important**: If you're not using the default service names, you must edit the manifest files before deployment:

- **Stage 2**: Edit `02-cf-quotes-postgres/manifest-uv.yml`
  - Update the `services` section with your PostgreSQL service instance name
  - Optionally set `VECTOR_DB_SERVICE_NAME` environment variable if your service name differs

- **Stage 3**: Edit `03-cf-quotes-semantic/manifest-uv.yml`
  - Update the `services` section with your PostgreSQL and embedding service instance names
  - Optionally set `VECTOR_DB_SERVICE_NAME` and `EMBEDDING_SERVICE_NAME` environment variables

- **Stage 4**: Edit `04-cf-quotes-mcp/manifest-uv.yml`
  - Update the `services` section with your PostgreSQL and embedding service instance names
  - Optionally set `VECTOR_DB_SERVICE_NAME` and `EMBEDDING_SERVICE_NAME` environment variables

Default service names used:
- `vector-db` - PostgreSQL service instance
- `tanzu-nomic-embed-text` - AI Embedding service instance (Stages 3 & 4)

## Quick Start

### Stage 1: Random Quotes (In-Memory)

**Purpose**: Learn basic Cloud Foundry deployment with no external dependencies.

```bash
cd 01-cf-quotes-random
cf push -f manifest-uv.yml
```

**Test Endpoints**:
```bash
# Get a random quote
curl https://cf-quotes-01-random-uv.<tpcf-apps-platform-url>/quote

# Get all quotes
curl https://cf-quotes-01-random-uv.<tpcf-apps-platform-url>/quotes

# Health check
curl https://cf-quotes-01-random-uv.<tpcf-apps-platform-url>/health
```

---

### Stage 2: Random Quotes with PostgreSQL

**Purpose**: Learn service marketplace, service creation, and service binding.

**Note**: Ensure your PostgreSQL service instance exists and matches the name in `manifest-uv.yml` (default: `vector-db`).

```bash
cd 02-cf-quotes-postgres
cf push -f manifest-uv.yml
```

**Test Endpoints**:
```bash
# Health check
curl https://cf-quotes-02-postgres-uv.<tpcf-apps-platform-url>/health

# Get a random quote
curl https://cf-quotes-02-postgres-uv.<tpcf-apps-platform-url>/quote

# Get all quotes
curl https://cf-quotes-02-postgres-uv.<tpcf-apps-platform-url>/quotes

# Initialize database with quotes
curl -X POST https://cf-quotes-02-postgres-uv.<tpcf-apps-platform-url>/quotes/init

# Clean database
curl -X POST https://cf-quotes-02-postgres-uv.<tpcf-apps-platform-url>/quotes/clean
```

---

### Stage 3: Semantic Quotes Search

**Purpose**: Learn vector embeddings, semantic search, and AI integration.

**Note**: Ensure your PostgreSQL and embedding service instances exist and match the names in `manifest-uv.yml` (defaults: `vector-db` and `bge-small-en-v1_5`).

```bash
cd 03-cf-quotes-semantic
cf push -f manifest-uv.yml
```

**Test Endpoints**:
```bash
# Health check
curl https://cf-quotes-03-semantic-uv.<tpcf-apps-platform-url>/health

# Get all quotes
curl https://cf-quotes-03-semantic-uv.<tpcf-apps-platform-url>/quotes

# Semantic search by topic
curl "https://cf-quotes-03-semantic-uv.<tpcf-apps-platform-url>/quotes?topic=kindness"

# Semantic search with complex query
curl "https://cf-quotes-03-semantic-uv.<tpcf-apps-platform-url>/quotes?topic=The%20roots%20of%20education%20are%20bitter%20but%20the%20fruit%20is%20sweet"

# Initialize database with quotes and embeddings
curl -X POST https://cf-quotes-03-semantic-uv.<tpcf-apps-platform-url>/quotes/init

# Clean database
curl -X POST https://cf-quotes-03-semantic-uv.<tpcf-apps-platform-url>/quotes/clean
```

---

### Stage 4: MCP Integration

**Purpose**: Learn Model Context Protocol (MCP) integration for AI agent capabilities.

**Note**: Ensure your PostgreSQL and embedding service instances exist and match the names in `manifest-uv.yml` (defaults: `vector-db` and `tanzu-nomic-embed-text`).

```bash
cd 04-cf-quotes-mcp
cf push -f manifest-uv.yml
```

**Test Endpoints**:
```bash
# Health check
curl https://cf-quotes-04-mcp-uv.<tpcf-apps-platform-url>/health

# MCP endpoint
curl https://cf-quotes-04-mcp-uv.<tpcf-apps-platform-url>/mcp
```

---

## Complete Testing Flow

Follow this sequence to test all four stages:

### 1. Deploy and Test Stage 1
```bash
cd 01-cf-quotes-random
cf push -f manifest-uv.yml
curl https://cf-quotes-01-random-uv.<tpcf-apps-platform-url>/quote
```

### 2. Deploy and Test Stage 2
```bash
cd 02-cf-quotes-postgres
# Edit manifest-uv.yml if your service name differs from 'vector-db'
cf push -f manifest-uv.yml
curl https://cf-quotes-02-postgres-uv.<tpcf-apps-platform-url>/health
curl -X POST https://cf-quotes-02-postgres-uv.<tpcf-apps-platform-url>/quotes/init
curl https://cf-quotes-02-postgres-uv.<tpcf-apps-platform-url>/quote
```

### 3. Deploy and Test Stage 3
```bash
cd 03-cf-quotes-semantic
# Edit manifest-uv.yml if your service names differ from defaults
cf push -f manifest-uv.yml
curl https://cf-quotes-03-semantic-uv.<tpcf-apps-platform-url>/health
curl -X POST https://cf-quotes-03-semantic-uv.<tpcf-apps-platform-url>/quotes/init
curl "https://cf-quotes-03-semantic-uv.<tpcf-apps-platform-url>/quotes?topic=kindness"
```

### 4. Deploy and Test Stage 4
```bash
cd 04-cf-quotes-mcp
# Edit manifest-uv.yml if your service names differ from defaults
cf push -f manifest-uv.yml
curl https://cf-quotes-04-mcp-uv.<tpcf-apps-platform-url>/health
curl https://cf-quotes-04-mcp-uv.<tpcf-apps-platform-url>/mcp
```

## Project Structure

```
demo-gto-python-cf/
├── 01-cf-quotes-random/      # Stage 1: In-memory quotes
│   ├── app.py
│   ├── quotes.py
│   ├── manifest-uv.yml
│   └── README.md
├── 02-cf-quotes-postgres/    # Stage 2: PostgreSQL integration
│   ├── app.py
│   ├── database.py
│   ├── manifest-uv.yml
│   └── README.md
├── 03-cf-quotes-semantic/    # Stage 3: Semantic search
│   ├── app.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── manifest-uv.yml
│   └── README.md
├── 04-cf-quotes-mcp/         # Stage 4: MCP integration
│   ├── app.py
│   ├── manifest-uv.yml
│   └── README.md
└── README.md                 # This file
```

## Key Concepts Learned

### Stage 1
- Basic `cf push` deployment
- Application health checks
- Route management
- Application logging

### Stage 2
- Service marketplace (`cf marketplace`)
- Service instance creation (`cf create-service`)
- Service binding (`cf bind-service`)
- `VCAP_SERVICES` environment variable
- Service credential injection

### Stage 3
- Vector embeddings generation
- Semantic similarity search
- AI/ML service integration
- Advanced database queries

### Stage 4
- Model Context Protocol (MCP)
- AI agent capabilities
- Tool calling and function execution

## Common Commands

### View Application Logs
```bash
# Real-time logs
cf logs <app-name>

# Recent logs
cf logs <app-name> --recent
```

### Check Application Status
```bash
# List all applications
cf apps

# View application details
cf app <app-name>
```

### View Routes
```bash
cf routes
```

### Scale Application
```bash
cf scale <app-name> -i <instances>
```

## Troubleshooting

1. **Application fails to start**: Check logs with `cf logs <app-name> --recent`
2. **Service binding issues**: 
   - Verify service exists with `cf services`
   - Check that service names in `manifest-uv.yml` match your service instance names
   - Verify environment variables (`VECTOR_DB_SERVICE_NAME`, `EMBEDDING_SERVICE_NAME`) if using custom service names
3. **Route conflicts**: Check existing routes with `cf routes`
4. **Buildpack issues**: Ensure `runtime.txt` specifies correct Python version

## Next Steps

Each project directory contains a detailed README with:
- Architecture diagrams
- API documentation
- Deployment options
- Advanced configuration

For more information, see the individual README files in each project directory.

---

**Total Stages**: 4 | **Complexity**: Progressive (Basic → Advanced)


## Resources

Documentation for the platform components used in this workshop:

- **Tanzu Postgres (Postgres tile)**
  - [Tanzu for Postgres on Tanzu Platform](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/tanzu-postgres-tanzu-platform/1-2/postgres-tp/install.html) — tile install and configuration

- **Tanzu AI Services**
  - [AI Services](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/ai-services/10-3/ai/index.html) — overview, embedding models, and integrations
  - [Binding credentials format (GenAI on TAS for Cloud Foundry)](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform-services/genai-on-tanzu-platform-for-cloud-foundry/10-3/ai-cf/reference-binding-credentials-format.html) — `VCAP_SERVICES` and model capabilities (e.g. embedding)

- **Elastic Application Runtime (TAS)**
  - [Elastic Application Runtime — concepts overview](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/elastic-application-runtime/10-3/eart/concepts-overview.html) — runtime architecture and components
