#!/bin/bash

# Handle Ctrl+C signal
trap 'echo -e "\nShutting down all servers..."; kill $PID_ALPHA $PID_BETA 2>/dev/null; exit 0' SIGINT

echo "Starting server 1 (port 9011)..."
fastmcp run mcp/server/user_mcp_server.py --transport http --port 9011 &
PID_ALPHA=$!

echo "Starting server 2 (port 9012)..."
fastmcp run mcp/server/prod_mcp_server.py --transport http --port 9012 &
PID_BETA=$!

echo "Both servers are running. Press Ctrl+C to terminate."
echo "Server1 PID: $PID_ALPHA"
echo "Server2 PID: $PID_BETA"

# Wait until processes terminate
wait