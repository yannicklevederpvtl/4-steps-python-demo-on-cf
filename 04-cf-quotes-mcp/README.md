# Stage 4: Semantic Quotes MCP Server - MCP Protocol Integration

A FastMCP standalone server demonstrating Model Context Protocol (MCP) integration. This stage transforms the quote functionality into an MCP server with HTTP/SSE transport, exposing tools via the MCP protocol.

## Overview

**Purpose**: Learn MCP protocol and FastMCP framework
- **MCP Protocol**: Standardized protocol for AI model interaction with external tools
- **FastMCP Framework**: Standalone MCP server framework (replaces FastAPI for MCP)
- **HTTP/SSE Transport**: Server-Sent Events for streaming MCP communication
- **MCP Tools**: Expose quote functionality as discoverable MCP tools
- **Gateway Integration**: Connect to MCP gateways and clients

**Technology Stack**:
- FastMCP: Standalone MCP server framework
- PostgreSQL + pgvector: Vector database for embeddings
- AI Embedding Service: Generate text embeddings
- LangChain: Framework for LLM applications
- Python 3.11+: Runtime environment

## Architecture

```
┌─────────────────────────────────────┐
│      FastMCP Server                 │
│  ┌───────────────────────────────┐  │
│  │  MCP Tools (via @mcp.tool):   │  │
│  │  • search_quotes              │  │
│  │  • get_random_quote           │  │
│  │  • get_all_quotes             │  │
│  │  • compare_words              │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  MCP Protocol (automatic):    │  │
│  │  • HTTP/SSE transport         │  │
│  │  • JSON-RPC messages          │  │
│  │  • Tool routing               │  │
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

## MCP Tools

The server exposes 4 MCP tools for quote functionality:

### search_quotes
Search for quotes by topic using semantic similarity.

**Parameters**:
- `topic` (string): Topic to search for (e.g., "education", "kindness")
- `k` (integer, optional): Number of results (default: 10, max: 24)

**Returns**: List of quotes with similarity scores

### get_random_quote
Get a random inspirational quote.

**Parameters**: None

**Returns**: Single quote with text and category

### get_all_quotes
Get all quotes from the database.

**Parameters**: None

**Returns**: List of all quotes

### compare_words
Compare two words for semantic similarity.

**Parameters**:
- `word1` (string): First word
- `word2` (string): Second word

**Returns**: Similarity score (0.0 to 1.0)

## Testing

### Testing with MCP Inspector

MCP Inspector is a visual tool for testing MCP servers interactively.

1. **Start the server**:
   ```bash
   python app.py
   # Or after deployment:
   # Server runs at: https://cf-quotes-mcp-04.apps.your-domain.com
   ```

2. **Connect with MCP Inspector**:
   - Open MCP Inspector
   - Connect to: `http://localhost:8080` (local) or deployed URL
   - Verify connection is established

3. **Test tools**:
   - View available tools in MCP Inspector
   - Test each tool interactively:
     - `search_quotes`: Enter topic "education", verify results
     - `get_random_quote`: Call and verify response
     - `get_all_quotes`: Verify all quotes returned
     - `compare_words`: Test "king" vs "queen" similarity
   - Verify tool schemas match expected parameters
   - Check error handling with invalid inputs

### Testing with MCP Client

You can also test programmatically using an MCP client:

```python
from fastmcp import FastMCPClient

# Connect to server
client = FastMCPClient("http://localhost:8080")
client.initialize()

# List available tools
tools = client.list_tools()
print(f"Available tools: {[t.name for t in tools]}")

# Call a tool
result = client.call_tool("search_quotes", {"topic": "education", "k": 5})
print(result)
```

## Gateway Integration

MCP gateways can connect to this server via HTTP/SSE:

1. **Server URL**: `https://cf-quotes-mcp-04.apps.your-domain.com`
2. **Transport**: HTTP/SSE (Server-Sent Events)
3. **Protocol**: MCP (Model Context Protocol)
4. **Tools**: All 4 tools are automatically discoverable

The gateway will:
- Connect via HTTP/SSE transport
- Discover available tools via `tools/list`
- Call tools via `tools/call` with JSON-RPC messages
- Receive responses as SSE events

## Project Structure

```
cf-quotes-mcp-04/
├── app.py              # FastMCP server application
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

## FastMCP Framework

FastMCP is a standalone MCP server framework that simplifies MCP implementation:

- **No FastAPI needed**: FastMCP is a complete server framework
- **Automatic HTTP/SSE**: Handles transport automatically
- **Automatic JSON-RPC**: Parses and formats MCP messages
- **Tool registration**: Just use `@mcp.tool` decorator
- **Protocol compliance**: Handles all MCP protocol complexity

## Previous Stage

**Stage 3**: Semantic Quotes with PostgreSQL
- FastAPI REST API
- Vector similarity search
- AI embedding services
- PostgreSQL with pgvector

## Next Stage

This is the final stage of the demo series.

---

**Stage**: 4 of 4 | **Complexity**: Advanced | **Services**: PostgreSQL + AI Embedding | **Protocol**: MCP
