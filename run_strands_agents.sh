#!/bin/bash

# Handle Ctrl+C signal
trap 'echo -e "\nShutting down all agents..."; kill $PID_BETA $PID_GAMMA $PID_DELTA $PID_HOST 2>/dev/null; exit 0' SIGINT

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

echo "Starting User Agent (port 9101)..."
uv run strands_agents/user_agent.py &
PID_BETA=$!

echo "Starting Product Agent (port 9102)..."
uv run strands_agents/product_agent.py &
PID_GAMMA=$!

echo "Starting Travel Guide Agent (port 9103)..."
uv run strands_agents/travel_guide_agent.py &
PID_DELTA=$!

# Wait for all three agents to be ready
wait_for_port 9101 "User Agent"
wait_for_port 9102 "Product Agent"
wait_for_port 9103 "Travel Guide Agent"

echo ""
echo "All base agents are ready. Starting Host Agent..."
echo "Starting Host Agent with FastAPI (port 9201)..."
uv run strands_agents/host_agent.py &
PID_HOST=$!

wait_for_port 9201 "Host Agent"

echo ""
echo "All agents are running. Press Ctrl+C to terminate."
echo "User Agent PID: $PID_BETA"
echo "Product Agent PID: $PID_GAMMA"
echo "Travel Guide Agent PID: $PID_DELTA"
echo "Host Agent PID: $PID_HOST"

# Wait until processes terminate
wait