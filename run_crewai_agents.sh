#!/bin/bash

# Handle Ctrl+C signal
trap 'echo -e "\nShutting down all agents..."; kill $PID_USER $PID_PRODUCT $PID_TRAVEL_GUIDE $PID_TRAVEL_PLANNER 2>/dev/null; exit 0' SIGINT

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

echo "Starting CrewAI User Agent (port 9101)..."
uv run crew_agents/user_agent/crew.py &
PID_USER=$!

echo ""
echo "Starting CrewAI Product Agent (port 9102)..."
uv run crew_agents/product_agent/crew.py &
PID_PRODUCT=$!

echo ""
echo "Starting CrewAI Travel Guide Agent (port 9103)..."
uv run crew_agents/travel_guide_agent/crew.py &
PID_TRAVEL_GUIDE=$!

echo ""
echo "Starting CrewAI Travel Planner Agent (port 10002)..."
uv run crew_agents/travel_planner_agent/crew.py &
PID_TRAVEL_PLANNER=$!

# Wait for agent to be ready
wait_for_port 9101 "CrewAI User Agent"
wait_for_port 9102 "CrewAI Product Agent"
wait_for_port 9103 "CrewAI Travel Guide Agent"
wait_for_port 10002 "CrewAI Travel Planner Agent"

echo ""
echo "Starting CrewAI Host Agent (port 10000)..."
uv run crew_agents/host_agent/crew.py &
PID_HOST=$!

wait_for_port 10000 "CrewAI Host Agent"

echo ""
echo "All CrewAI agents are running. Press Ctrl+C to terminate."
echo "User Agent PID: $PID_USER (port 9101)"
echo "Product Agent PID: $PID_PRODUCT (port 9102)"
echo "Travel Guide Agent PID: $PID_TRAVEL_GUIDE (port 9103)"
echo "Travel Planner Agent PID: $PID_TRAVEL_PLANNER (port 10002)"
echo "HOST Agent PID: $PID_HOST (port 10000)"

# Wait until processes terminate
wait
