#!/bin/bash

# Handle Ctrl+C signal
trap 'echo -e "\nShutting down all agents..."; kill $PID_BETA $PID_GAMMA $PID_ALPHA 2>/dev/null; exit 0' SIGINT

echo "Starting agent 1 (port 9103)..."
uv run mcp/agent/travel_guide_agent/travel_guide_agent.py &
PID_BETA=$!

echo "Starting agent 2 (port 9104)..."
uv run mcp/agent/travel_planner_agent/travel_planner_agent.py &
PID_GAMMA=$!

echo "Starting agent 3 (port 9202)..."
uv run host/travel_assistant_agent/agent.py &
PID_ALPHA=$!

echo "all Agent are running. Press Ctrl+C to terminate."
echo "Agent 1 PID: $PID_BETA"
echo "Agent 2 PID: $PID_GAMMA"
echo "Agent 3 PID: $PID_ALPHA"

# Wait until processes terminate
wait