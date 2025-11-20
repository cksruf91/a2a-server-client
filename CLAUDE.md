# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

a2a-server-client is a multi-agent system implementing the Agent-to-Agent (A2A) protocol using Model Context Protocol (MCP) for tool integration. It demonstrates orchestration of specialized agents that communicate and collaborate to handle user requests.

### Architecture

The project consists of three layers:

1. **MCP Servers**: Provide domain-specific tools (user/product/travel information)
2. **A2A Agents**: Specialized agents that use MCP tools to handle specific domains
   - Strands-based agents (user, product)
   - Google ADK-based agents (travel guide, planner, assistant)
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
- `google-adk`: Google Agent Development Kit (for google-based agents)
- `litellm`: LLM abstraction layer (used with google-adk agents)
- `nest-asyncio`: Nested asyncio support for compatibility

## Project Structure

```
a2a-server-client/
├── strands_app.py                      # FastAPI web app (port 9201)
├── strands_agents/
│   ├── host_agent.py                  # StrandsHostAgent orchestrator
│   ├── user_agent.py                  # User information agent (port 9101)
│   └── product_agent.py               # Product information agent (port 9102)
├── google_agents/
│   ├── travel_guide_agent/
│   │   └── agent.py                   # Travel guide agent (port 10001)
│   ├── travel_planner_agent/
│   │   └── agent.py                   # Travel planner agent (port 10002)
│   └── travel_assistant_agent/
│       └── agent.py                   # Travel assistant agent (port 10000)
├── mcp/
│   └── server/
│       ├── user_mcp_server.py         # User info MCP server (port 9011)
│       ├── prod_mcp_server.py         # Product info MCP server (port 9012)
│       └── travel_mcp_server.py       # Travel info MCP server with Gemini grounding (port 5001)
├── common/
│   └── google/
│       ├── abstract_agent.py          # Base class for Google ADK agents
│       ├── executor.py                # GenericAgentExecutor for A2A integration
│       ├── tool.py                    # ToolFilter for MCP tool filtering by tags
│       └── types.py                   # Type definitions for agent responses
├── resource/
│   ├── prompt.yaml                    # System prompts for agents (Korean)
│   └── app/
│       ├── index.html                 # Chat UI frontend
│       ├── app.js                     # Frontend JavaScript (API_BASE_URL: port 9201)
│       └── README.md                  # Frontend documentation
├── run_strands_agents.sh              # Script to start strands agents
├── run_google_agents.sh               # Script to start google agents
├── run_mcp_server.sh                  # Script to start all MCP servers
├── pyproject.toml                     # Project metadata and dependencies
└── uv.lock                            # Locked dependency versions
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

# Terminal 2 - Start Strands agents (user, product)
./run_strands_agents.sh

# Terminal 3 - Start Google agents (travel guide, planner, assistant)
./run_google_agents.sh

# Terminal 4 - Start web application
uv run uvicorn strands_app:main --reload --host 0.0.0.0 --port 9201
```

#### Option 2: Manual Start
```bash
# Start MCP servers
fastmcp run mcp/server/user_mcp_server.py --transport http --port 9011
fastmcp run mcp/server/prod_mcp_server.py --transport http --port 9012
fastmcp run mcp/server/travel_mcp_server.py --transport http --port 5001

# Start Strands agents
uv run strands_agents/user_agent.py
uv run strands_agents/product_agent.py

# Start Google agents
uv run google_agents/travel_guide_agent/agent.py
uv run google_agents/travel_planner_agent/agent.py
uv run google_agents/travel_assistant_agent/agent.py

# Start web app
uv run uvicorn strands_app:main --reload --host 0.0.0.0 --port 9201
```

### Accessing the Application

- Web UI: http://localhost:9201
- Web UI (alternate): http://localhost:9201/index
- Strands User Agent (A2A): http://localhost:9101
- Strands Product Agent (A2A): http://localhost:9102
- Google Travel Guide Agent (A2A): http://localhost:10001
- Google Travel Planner Agent (A2A): http://localhost:10002
- Google Travel Assistant Agent (A2A): http://localhost:10000

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

### MCP Servers (Ports 9011-9012, 5001)
- `user_mcp_server.py` (port 9011): Provides tools for user information access
- `prod_mcp_server.py` (port 9012): Provides tools for product information access
- `travel_mcp_server.py` (port 5001): Provides travel tools using Gemini with Google Maps grounding
  - Uses `MapGroundingAgent` with Gemini 2.5 Flash Lite
  - Tools tagged with `{'travel', 'guide'}` for selective loading
  - `get_place_recommendation`: Get tourist attraction recommendations by city/country
  - `get_place_information`: Get detailed information about landmarks
  - `get_tour_plan`: Generate multi-day travel itineraries

### A2A Agents

#### Strands-based Agents (Ports 9101-9102)
Located in `strands_agents/`:
- `user_agent.py` (port 9101): Handles user-related queries using MCP user tools
- `product_agent.py` (port 9102): Handles product-related queries using MCP product tools
- Both extend `MCPAgentWithClient` from strands-agents
- Use `MCPClientSession` to connect to MCP servers
- Tool registration via `MCPToolProvider`

#### Google ADK-based Agents (Ports 10001, 10002, 10000)
Located in `google_agents/`:
- `travel_guide_agent/agent.py` (port 10001): Provides travel guide information
  - Filters tools by tag: `'guide'`
- `travel_planner_agent/agent.py` (port 10002): Plans travel itineraries
  - Filters tools by tag: `'planner'`
- `travel_assistant_agent/agent.py` (port 10000): General travel assistance
  - Filters tools by tag: `'travel'`

**Google ADK Agent Architecture**:
- Extend `AbstractAgent` base class (`common/google/abstract_agent.py`)
- Use `LiteLlm` with GPT-4o-mini as the model
- Connect to travel MCP server via `StreamableHTTPConnectionParams`
- Use custom `ToolFilter` (`common/google/tool.py`) for tag-based tool filtering
- Implement `BuiltInPlanner` with `ThinkingConfig` for reasoning
- Session management via `InMemorySessionService`
- Bridge to A2A using `GenericAgentExecutor` (`common/google/executor.py`)
- Streaming responses using `AgentResponse` type

### Host Agent & Web Application

- `strands_agents/host_agent.py`: StrandsHostAgent implementation
  - Orchestrates A2A agents using strands-agents framework
  - Uses `A2AClientToolProvider` for agent communication
  - Configured to connect to agents at ports 9101 and 9102 (Strands agents only)
  - Provides both complete and streaming chat endpoints
  - Loads system prompts from `resource/prompt.yaml`
  - Implements custom `A2AExecutor` for task execution
  - Handles chat history and session management

- `strands_app.py`: FastAPI-based web application (port 9201)
  - Imports and uses `StrandsHostAgent` from `strands_agents/host_agent.py`
  - Exposes REST API endpoints: `/chat/complete` and `/chat/stream`
  - Serves static frontend files from `resource/app/` at `/static`
  - Provides `/index` endpoint serving the chat UI
  - Mounts A2A application for protocol compliance
  - CORS enabled for frontend-backend communication

### Frontend
- Single-page application with chat interface
- Located in `resource/app/`
- Connects to FastAPI backend on port 9201
- Supports both normal (complete) and streaming chat modes
- Session management with localStorage persistence

## Port Reference

| Component | Port | Description |
|-----------|------|-------------|
| Web App (FastAPI) | 9201 | StrandsHostAgent with UI (via strands_app.py) |
| Strands User Agent | 9101 | User information agent |
| Strands Product Agent | 9102 | Product information agent |
| Google Travel Guide Agent | 10001 | Travel guide (filters tag: 'guide') |
| Google Travel Planner Agent | 10002 | Travel planner (filters tag: 'planner') |
| Google Travel Assistant Agent | 10000 | Travel assistant (filters tag: 'travel') |
| User MCP Server | 9011 | User info tools |
| Product MCP Server | 9012 | Product info tools |
| Travel MCP Server | 5001 | Travel info tools with Gemini grounding |

## Agent Implementation Patterns

### Strands-based Agents
Pattern used in `strands_agents/user_agent.py` and `strands_agents/product_agent.py`:
- Extend `MCPAgentWithClient` from strands-agents
- Use `MCPClientSession` to connect to MCP servers
- Tool registration via `MCPToolProvider`
- A2A protocol handled automatically by strands framework
- Runs as standalone A2A server

### Google ADK-based Agents
Pattern used in all agents under `google_agents/`:
- Extend custom `AbstractAgent` base class (`common/google/abstract_agent.py`)
- Use `LiteLlm` with GPT-4o-mini model
- Connect to MCP server via `McpToolset` with `StreamableHTTPConnectionParams`
- Use `ToolFilter` (`common/google/tool.py`) to filter tools by tags
- Implement `BuiltInPlanner` with `ThinkingConfig` for agent reasoning
- Session management via `InMemorySessionService`
- Bridge to A2A using `GenericAgentExecutor` (`common/google/executor.py`)
- Implement async `stream()` method yielding `AgentResponse` objects
- Manual A2A event handling (task updates, artifacts, status)

**Key difference**: Google ADK agents require custom executor and response handling to bridge between Google ADK's `Event` system and A2A's task/event model. The `GenericAgentExecutor` translates Google ADK events into A2A protocol messages.

## Development Notes

### Environment Variables
- `OPENAI_API_KEY`: Required for OpenAI LLM (strands agents and Google ADK agents using LiteLlm)
- `GOOGLE_API_KEY` or `GOOGLE_GENAI_API_KEY`: Required for Gemini models in travel MCP server

### Architecture Notes
- **Agent Communication**: Agents communicate via A2A protocol over HTTP
- **Tool Provision**: Tools are provided via MCP (Model Context Protocol) servers
- **Host Agent Limitation**: StrandsHostAgent currently only connects to Strands agents (ports 9101, 9102), not Google ADK agents
- **MCP Tool Tagging**: Tools in travel MCP server are tagged (`'guide'`, `'planner'`, `'travel'`) for selective loading by different agents
- **System Prompts**: Defined in `resource/prompt.yaml` (Korean language)
- **Frontend Features**:
  - Supports both complete and streaming chat modes
  - Session persistence using browser localStorage
  - Chat history maintained per session
- **CORS**: Enabled for frontend-backend communication

### Adding New Agents

#### For Strands-based agents:
1. Create MCP server in `mcp/server/` with tools (if needed)
2. Create agent file in `strands_agents/` extending `MCPAgentWithClient`
3. Configure MCP connection via `MCPClientSession`
4. Choose a unique port for the agent
5. Add to `run_strands_agents.sh` startup script
6. Update `StrandsHostAgent.AGENT_URLS` in `strands_agents/host_agent.py` to include the new agent

#### For Google ADK-based agents:
1. Create MCP server with tagged tools in `mcp/server/` (if needed)
2. Create agent directory under `google_agents/` with `agent.py` and `__init__.py`
3. Extend `AbstractAgent` from `common/google/abstract_agent.py`
4. Configure `McpToolset` with `ToolFilter` for tag-based tool loading
5. Set up `GenericAgentExecutor` for A2A integration
6. Implement async `stream()` method yielding `AgentResponse`
7. Choose a unique port for the agent
8. Add to `run_google_agents.sh` startup script

### Tool Tag Management
When adding tools to `travel_mcp_server.py`, use appropriate tags:
- `'guide'`: For tourist attraction and place information (used by travel_guide_agent)
- `'planner'`: For itinerary planning (used by travel_planner_agent)
- `'travel'`: For general travel assistance (used by travel_assistant_agent)

Use the `@mcp.tool(tags={...})` decorator to tag tools appropriately.
- to memorize