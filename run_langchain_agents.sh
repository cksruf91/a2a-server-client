#!/bin/bash

# Handle Ctrl+C signal
trap 'echo -e "\nShutting down all agents..."; kill $PID_HOST &PID_ALPHA 2>/dev/null; exit 0' SIGINT

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

#echo "Starting User Agent (port 10003)..."
uv run langchain_agents/user_agent.py &
PID_ALPHA=$!

wait_for_port 10003 "User Information Agent"

# Wait for all four agents to be ready

echo ""
echo "All base agents are ready. Starting Host Agent..."
echo "Starting Host Agent (port 10000)..."
uv run langchain_agents/host_agent.py &
PID_HOST=$!

wait_for_port 10000 "Host Agent"

echo ""
echo "All agents are running. Press Ctrl+C to terminate."
echo "Host Agent PID: $PID_HOST"

# Wait until processes terminate
wait