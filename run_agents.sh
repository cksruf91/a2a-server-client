#!/bin/bash

# Handle Ctrl+C signal
#trap 'echo -e "\nShutting down all agents..."; kill $PID_ALPHA $PID_BETA $PID_GAMMA 2>/dev/null; exit 0' SIGINT
trap 'echo -e "\nShutting down all agents..."; kill $PID_BETA $PID_GAMMA 2>/dev/null; exit 0' SIGINT

#echo "Starting Host agent (port 9200)..."
#uv run host_agent.py &
#PID_ALPHA=$!

echo "Starting agent 1 (port 9101)..."
uv run mcp/agent/user_agent.py &
PID_BETA=$!

echo "Starting agent 2 (port 9102)..."
uv run mcp/agent/product_agent.py &
PID_GAMMA=$!

echo "all Agent are running. Press Ctrl+C to terminate."
#echo "Agent 1 PID: $PID_ALPHA"
echo "Agent 2 PID: $PID_BETA"
echo "Agent 2 PID: $PID_GAMMA"

# Wait until processes terminate
wait