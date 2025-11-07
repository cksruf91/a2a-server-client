# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

a2a-server-client is a multi-agent system implementing the Agent-to-Agent (A2A) protocol using Model Context Protocol (MCP) for tool integration. It demonstrates orchestration of specialized agents that communicate and collaborate to handle user requests.

### Architecture

The project consists of three layers:

1. **MCP Servers**: Provide domain-specific tools (user/product information)
2. **A2A Agents**: Specialized agents that use MCP tools to handle specific domains
3. **Web Application**: FastAPI app with StrandsHostAgent (host agent) and chat UI for user interaction

## Development Environment

- Python version: 3.12 (specified in `.python-version`)
- Package manager: `uv` (modern Python package installer and resolver)
- Virtual environment: `.venv/` (managed by uv)

## Key Dependencies

- `a2a-sdk`: Agent-to-Agent protocol implementation
- `fastmcp`: MCP (Model Context Protocol) server framework
- `strands-agents`: Agent framework with A2A client and MCP support
- `strands-agents-tools[a2a-client]`: A2A client tool provider for orchestration
- `fastapi` + `uvicorn`: Web framework and ASGI server
- `openai`: LLM integration (GPT-4o-mini)
- `google-adk`: Google Agent Development Kit
- `nest-asyncio`: Nested asyncio support for compatibility

## Project Structure

```
a2a-server-client/
├── app.py                          # FastAPI web app (port 9201) - imports from host/
├── prompt_manager.py               # Prompt management utility
├── host/
│   └── host_agent.py              # Host agent using strands-agents (port 9202 standalone)
├── mcp/
│   ├── agent/
│   │   ├── user_agent.py          # User information agent (port 9101)
│   │   └── product_agent.py       # Product information agent (port 9102)
│   └── server/
│       ├── user_mcp_server.py     # User info MCP server (port 9011)
│       └── prod_mcp_server.py     # Product info MCP server (port 9012)
├── resource/
│   ├── prompt.yaml                # System prompts for agents (Korean)
│   └── app/
│       ├── index.html             # Chat UI frontend
│       ├── app.js                 # Frontend JavaScript (API_BASE_URL: port 9201)
│       └── README.md              # Frontend documentation
├── run_agents.sh                   # Script to start all agents
├── run_mcp_server.sh              # Script to start all MCP servers
├── pyproject.toml                 # Project metadata and dependencies
└── uv.lock                        # Locked dependency versions
```

## Common Commands

### Environment Setup
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync
```

### Running the System

#### Option 1: Using Shell Scripts (Recommended)
```bash
# Terminal 1 - Start MCP servers
./run_mcp_server.sh

# Terminal 2 - Start A2A agents
./run_agents.sh

# Terminal 3 - Start web application (port 9201 matches app.js configuration)
uv run uvicorn app:main --reload --host 0.0.0.0 --port 9201
```

#### Option 2: Manual Start
```bash
# Start MCP servers
fastmcp run mcp/server/user_mcp_server.py --transport http --port 9011
fastmcp run mcp/server/prod_mcp_server.py --transport http --port 9012

# Start A2A agents
uv run mcp/agent/user_agent.py
uv run mcp/agent/product_agent.py

# Start web app (port 9201 matches app.js configuration)
uv run uvicorn app:main --reload --host 0.0.0.0 --port 9201
```

### Accessing the Application

- Web UI: http://localhost:9201
- User Agent (A2A): http://localhost:9101
- Product Agent (A2A): http://localhost:9102

### Dependency Management
```bash
# Add a new dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>

# Update dependencies
uv sync

# Show installed packages
uv pip list
```

## System Components

### MCP Servers (Ports 9011, 9012)
- `user_mcp_server.py`: Provides tools for user information access
- `prod_mcp_server.py`: Provides tools for product information access

### A2A Agents (Ports 9101, 9102)
- `user_agent.py`: Handles user-related queries using MCP user tools
- `product_agent.py`: Handles product-related queries using MCP product tools

### Host Agent & Web Application

- `host/host_agent.py`: StrandsHostAgent implementation
  - Orchestrates multiple A2A agents using strands-agents framework
  - Uses A2AClientToolProvider for agent communication
  - Provides both complete and streaming chat endpoints
  - Loads system prompts from `resource/prompt.yaml`
  - Can run standalone on port 9202 or via app.py

- `app.py`: FastAPI-based web application
  - Imports and uses StrandsHostAgent from `host/host_agent.py`
  - Exposes REST API endpoints: `/chat/complete` and `/chat/stream`
  - Serves static frontend files from `resource/app/`
  - Mounts A2A application for protocol compliance
  - Runs on port 9201 (matches frontend configuration)

### Frontend
- Single-page application with chat interface
- Located in `resource/app/`
- Connects to FastAPI backend on port 9201

## Port Reference

| Component | Port | Description |
|-----------|------|-------------|
| Web App (FastAPI) | 9201 | StrandsHostAgent with UI (via app.py) |
| Host Agent (Standalone) | 9202 | StrandsHostAgent standalone (host/host_agent.py) |
| User Agent (A2A) | 9101 | User information agent |
| Product Agent (A2A) | 9102 | Product information agent |
| User MCP Server | 9011 | User info tools |
| Product MCP Server | 9012 | Product info tools |

## Development Notes

- The system uses OpenAI GPT-4o-mini as the LLM backend
- Set `OPENAI_API_KEY` environment variable before running
- Agents communicate via A2A protocol
- Tools are provided via MCP (Model Context Protocol)
- CORS is enabled for frontend-backend communication
- System prompts are defined in `resource/prompt.yaml` (Korean language)
- Frontend supports both normal (complete) and streaming chat modes
- Chat sessions are persisted in browser localStorage

## Instruction
- Update this file if any change in code or project structure