# MCP Client Tester - Frontend App

Simple frontend application to test MCP (Model Context Protocol) client functionality.

## Overview

This is a single-page web application that provides a chat interface to interact with the MCP client backend. It demonstrates:
- Chat interface for sending messages to the MCP client
- Non-streaming and streaming response modes
- Tool discovery and listing
- Real-time message display

## Features

- **Chat Interface**: Clean, modern chat UI for interacting with the MCP assistant
- **Dual Mode Support**:
  - **Normal Mode**: Uses `/chat/main` endpoint (non-streaming)
  - **Stream Mode**: Uses `/chat/main/stream` endpoint (Server-Sent Events)
- **Tool Discovery**: View all available MCP tools via `/tool/list` endpoint
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### Prerequisites

1. MCP servers must be running:
```bash
# Terminal 1 - Alpha server
cd core/server
fastmcp run alpha.py --transport http --port 9011

# Terminal 2 - Beta server
cd core/server
fastmcp run beta.py --transport http --port 9012
```

2. MCP client (FastAPI) must be running:
```bash
# Terminal 3 - Client
cd core/client
uvicorn client:main --reload
```

### Running the Frontend

Simply open the HTML file in your browser:

```bash
cd core/app
open index.html
```

Or use a simple HTTP server:

```bash
cd core/app
python -m http.server 8080
# Then open http://localhost:8080 in your browser
```

## Usage

1. **Send Messages**: Type your message in the input field and press Enter or click Send
2. **Toggle Mode**: Switch between Normal and Stream modes using the toggle buttons
3. **View Tools**: Click "View Tools" button in the header to see all available MCP tools
4. **Example Queries**:
   - "What is the user's name?"
   - "What is the user's address?"
   - "Calculate the final price for item X"

## Technical Details

### API Endpoints Used

- `GET /ping` - Health check
- `GET /tool/list` - Get available MCP tools
- `POST /chat/main` - Send chat message (non-streaming)
- `POST /chat/main/stream` - Send chat message (streaming with SSE)

### Configuration

Default API base URL: `http://localhost:8000`

To change the API URL, edit the `API_BASE_URL` constant in the HTML file:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

### Browser Compatibility

- Modern browsers with ES6+ support
- Chrome 60+
- Firefox 60+
- Safari 12+
- Edge 79+

## File Structure

```
core/app/
├── index.html    # Single-page application (HTML + CSS + JavaScript)
└── README.md     # This file
```

## Troubleshooting

### CORS Errors

If you see CORS errors in the browser console, ensure:
1. The FastAPI client has CORS middleware enabled (already configured in `core/client/client.py`)
2. The client server is running on port 8000

### Connection Errors

If messages fail to send:
1. Check that the FastAPI client is running: `curl http://localhost:8000/ping`
2. Verify MCP servers are running on ports 9011 and 9012
3. Check browser console for detailed error messages

### No Tools Displayed

If the tools list is empty:
1. Ensure both MCP servers (alpha and beta) are running
2. Check server configuration in `core/client/common/service.py`
3. Verify `OPENAI_API_KEY` environment variable is set

## Development

The app is built with vanilla JavaScript for simplicity. To add features:

1. **Add new API endpoints**: Update the API calls in the `<script>` section
2. **Customize styling**: Modify the `<style>` section
3. **Add new UI components**: Edit the HTML structure

## License

Part of the MCP example project.