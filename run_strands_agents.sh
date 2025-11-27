#!/bin/bash

# Handle Ctrl+C signal
trap 'echo -e "\nShutting down all agents..."; kill $PID_BETA $PID_GAMMA $PID_DELTA 2>/dev/null; exit 0' SIGINT

echo "Starting agent 1 (port 9101)..."
uv run strands_agents/user_agent.py &
PID_BETA=$!

echo "Starting agent 2 (port 9102)..."
uv run strands_agents/product_agent.py &
PID_GAMMA=$!

echo "Starting agent 3 (port 9103)..."
uv run strands_agents/travel_guide_agent.py &
PID_DELTA=$!

echo "all Agent are running. Press Ctrl+C to terminate."
echo "Agent 1 PID: $PID_BETA"
echo "Agent 2 PID: $PID_GAMMA"
echo "Agent 3 PID: $PID_DELTA"

# Wait until processes terminate
wait