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
- `strands-agents`: Agent framework with A2A client and MCP support (used by host agent)
- `strands-agents-tools[a2a-client]`: A2A client tool provider for orchestration
- `fastapi` + `uvicorn`: Web framework and ASGI server
- `openai`: LLM integration (GPT-4o-mini for strands-based agents)
- `google-adk`: Google Agent Development Kit (for google-based agents like TravelGuideAgent)
- `litellm`: LLM abstraction layer (used with google-adk agents)
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
│   │   ├── product_agent.py       # Product information agent (port 9102)
│   │   └── travel_guide_agent.py  # Travel guide agent using Google ADK (port 9103)
│   └── server/
│       ├── user_mcp_server.py     # User info MCP server (port 9011)
│       ├── prod_mcp_server.py     # Product info MCP server (port 9012)
│       └── travel_mcp_server.py   # Travel info MCP server with Gemini grounding (port 9013)
├── common/
│   └── google/
│       ├── abstract_agent.py      # Base class for Google ADK agents
│       ├── executor.py            # GenericAgentExecutor for A2A integration
│       ├── tool.py                # ToolFilter for MCP tool filtering by tags
│       └── types.py               # Type definitions for agent responses
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
fastmcp run mcp/server/travel_mcp_server.py --transport http --port 9013

# Start A2A agents
uv run mcp/agent/user_agent.py
uv run mcp/agent/product_agent.py
uv run mcp/agent/travel_guide_agent.py

# Start web app (port 9201 matches app.js configuration)
uv run uvicorn app:main --reload --host 0.0.0.0 --port 9201
```

### Accessing the Application

- Web UI: http://localhost:9201
- User Agent (A2A): http://localhost:9101
- Product Agent (A2A): http://localhost:9102
- Travel Guide Agent (A2A): http://localhost:9103

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

### MCP Servers (Ports 9011-9013)
- `user_mcp_server.py` (port 9011): Provides tools for user information access
- `prod_mcp_server.py` (port 9012): Provides tools for product information access
- `travel_mcp_server.py` (port 9013): Provides travel tools using Gemini with Google Maps grounding
  - `get_place_recommendation`: Get tourist attraction recommendations by city/country
  - `get_place_information`: Get detailed information about landmarks
  - `get_tour_plan`: Generate multi-day travel itineraries

### A2A Agents (Ports 9101-9103)

#### Strands-based Agents (9101-9102)
- `user_agent.py`: Handles user-related queries using MCP user tools
- `product_agent.py`: Handles product-related queries using MCP product tools

#### Google ADK-based Agents (9103)
- `travel_guide_agent.py`: Travel guide using Google ADK framework
  - Uses LiteLlm with GPT-4o-mini
  - Connects to travel MCP server (port 9013) via StreamableHTTPConnectionParams
  - Filters tools by tags using custom ToolFilter (tag: 'guide')
  - Implements BuiltInPlanner with thinking config for reasoning
  - Session management via InMemorySessionService

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
| User Agent (A2A) | 9101 | User information agent (strands-based) |
| Product Agent (A2A) | 9102 | Product information agent (strands-based) |
| Travel Guide Agent (A2A) | 9103 | Travel guide agent (Google ADK-based) |
| User MCP Server | 9011 | User info tools |
| Product MCP Server | 9012 | Product info tools |
| Travel MCP Server | 9013 | Travel info tools with Gemini grounding |

## Agent Implementation Patterns

### Strands-based Agents (user_agent, product_agent)
- Extend `MCPAgentWithClient` from strands-agents
- Use `MCPClientSession` to connect to MCP servers
- Tool registration via `MCPToolProvider`
- A2A protocol handled by strands framework

### Google ADK-based Agents (travel_guide_agent)
- Extend custom `AbstractAgent` base class (`common/google/abstract_agent.py`)
- Use `GenericAgentExecutor` (`common/google/executor.py`) to integrate with A2A
- Custom `ToolFilter` to filter MCP tools by tags
- Session management via Google ADK's InMemorySessionService
- `AgentResponse` type for streaming responses
- Manual A2A event handling (task updates, artifacts, status)

**Key difference**: Google ADK agents require custom executor and response handling to bridge between Google ADK's `Event` system and A2A's task/event model.

## Development Notes

### Environment Variables
- `OPENAI_API_KEY`: Required for OpenAI LLM (strands agents and Google ADK agents using LiteLlm)
- `GOOGLE_API_KEY` or `GOOGLE_GENAI_API_KEY`: Required for Gemini models in travel MCP server

### Architecture Notes
- Agents communicate via A2A protocol
- Tools are provided via MCP (Model Context Protocol)
- CORS is enabled for frontend-backend communication
- System prompts are defined in `resource/prompt.yaml` (Korean language)
- Frontend supports both normal (complete) and streaming chat modes
- Chat sessions are persisted in browser localStorage
- MCP tool filtering by tags enables selective tool loading per agent

### Adding New Agents

#### For Strands-based agents:
1. Create MCP server in `mcp/server/` with tools
2. Create agent in `mcp/agent/` extending `MCPAgentWithClient`
3. Configure MCP connection via `MCPClientSession`
4. Add to `run_agents.sh` and `run_mcp_server.sh`

#### For Google ADK-based agents:
1. Create MCP server with tagged tools
2. Create agent extending `AbstractAgent`
3. Use `McpToolset` with `ToolFilter` for tag-based tool loading
4. Configure `GenericAgentExecutor` for A2A integration
5. Implement async `stream()` method yielding `AgentResponse`
6. Add to startup scripts

## Instruction
- Update this file if any change in code or project structure