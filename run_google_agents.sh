#!/bin/bash

# Handle Ctrl+C signal
trap 'echo -e "\nShutting down all agents..."; kill $PID_BETA $PID_GAMMA $PID_ALPHA 2>/dev/null; exit 0' SIGINT

echo "Starting agent 1 (port 10001)..."
uv run google_agents/travel_guide_agent/agent.py &
PID_BETA=$!

echo "Starting agent 2 (port 10002)..."
uv run google_agents/travel_planner_agent/agent.py &
PID_GAMMA=$!

echo "Starting Host Agent (port 10000)..."
uv run google_agents/host_agent/agent.py &
PID_ALPHA=$!

echo "all Agent are running. Press Ctrl+C to terminate."
echo "Agent 1 PID: $PID_BETA"
echo "Agent 2 PID: $PID_GAMMA"
echo "Agent 3 PID: $PID_ALPHA"

# Wait until processes terminate
wait