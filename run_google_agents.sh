#!/bin/bash

# Handle Ctrl+C signal
trap 'echo -e "\nShutting down all agents..."; kill $PID_USER $PID_PRODUCT $PID_GUIDE $PID_PLANNER $PID_HOST 2>/dev/null; exit 0' SIGINT

# Function to wait for a port to be ready
wait_for_port() {
    local port=$1
    local name=$2
    local max_attempts=60
    local attempt=0

    echo "Waiting for $name to be ready on port $port..."
    while ! nc -z localhost $port 2>/dev/null; do
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            echo "Warning: $name on port $port did not start within expected time"
            return 1
        fi
        sleep 1
    done
    echo "$name is ready!"
    return 0
}

echo "Starting User Agent (port 10003)..."
uv run google_agents/user_agent/agent.py &
PID_USER=$!

echo "Starting Product Agent (port 10004)..."
uv run google_agents/product_agent/agent.py &
PID_PRODUCT=$!

echo "Starting Travel Guide Agent (port 10001)..."
uv run google_agents/travel_guide_agent/agent.py &
PID_GUIDE=$!

echo "Starting Travel Planner Agent (port 10002)..."
uv run google_agents/travel_planner_agent/agent.py &
PID_PLANNER=$!

# Wait for all four agents to be ready
wait_for_port 10003 "User Agent"
wait_for_port 10004 "Product Agent"
wait_for_port 10001 "Travel Guide Agent"
wait_for_port 10002 "Travel Planner Agent"

echo ""
echo "All base agents are ready. Starting Host Agent..."
echo "Starting Host Agent (port 10000)..."
uv run google_agents/host_agent/agent.py &
PID_HOST=$!

wait_for_port 10000 "Host Agent"

echo ""
echo "All agents are running. Press Ctrl+C to terminate."
echo "User Agent PID: $PID_USER"
echo "Product Agent PID: $PID_PRODUCT"
echo "Travel Guide Agent PID: $PID_GUIDE"
echo "Travel Planner Agent PID: $PID_PLANNER"
echo "Host Agent PID: $PID_HOST"

# Wait until processes terminate
wait