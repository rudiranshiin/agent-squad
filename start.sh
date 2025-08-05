#!/bin/bash

# 🚀 Enhanced Agentic Framework - Development Startup Script
# This script starts both the backend and frontend development servers

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 Enhanced Agentic Framework 2.0${NC}"
echo -e "${CYAN}Starting development environment...${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Check dependencies
echo -e "${BLUE}🔍 Checking dependencies...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All dependencies found${NC}"

# Check if ports are available
if port_in_use 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use (backend)${NC}"
    echo -e "${YELLOW}   The existing service will be used${NC}"
fi

if port_in_use 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 is already in use (frontend)${NC}"
    echo -e "${YELLOW}   The existing service will be used${NC}"
fi

# Install Python dependencies if needed
if [ ! -f ".venv/bin/activate" ] && [ ! -f "venv/bin/activate" ]; then
    echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
    if command_exists pip3; then
        pip3 install -r requirements.txt
    else
        pip install -r requirements.txt
    fi
else
    echo -e "${GREEN}✅ Python virtual environment detected${NC}"
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
fi

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
    cd frontend
    npm install
    cd ..
else
    echo -e "${GREEN}✅ Frontend dependencies already installed${NC}"
fi

echo ""
echo -e "${GREEN}🎯 Starting services...${NC}"
echo ""

# Create log directory
mkdir -p logs

# Function to cleanup background processes
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}👋 Services stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${BLUE}🐍 Starting backend server (Port 8000)...${NC}"
if ! port_in_use 8000; then
    nohup uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
else
    echo -e "${YELLOW}⚠️  Backend already running on port 8000${NC}"
fi

# Wait a moment for backend to start
sleep 2

# Start frontend
echo -e "${BLUE}⚛️  Starting frontend server (Port 3000)...${NC}"
if ! port_in_use 3000; then
    cd frontend
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend already running on port 3000${NC}"
fi

# Wait for services to be ready
echo ""
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check if services are running
echo ""
echo -e "${GREEN}🎉 Services Status:${NC}"

if port_in_use 8000; then
    echo -e "${GREEN}✅ Backend API: http://localhost:8000${NC}"
    echo -e "${GREEN}📚 API Docs: http://localhost:8000/docs${NC}"
else
    echo -e "${RED}❌ Backend failed to start${NC}"
fi

if port_in_use 3000; then
    echo -e "${GREEN}✅ Frontend UI: http://localhost:3000${NC}"
else
    echo -e "${RED}❌ Frontend failed to start${NC}"
fi

echo ""
echo -e "${PURPLE}🎯 Quick Start Guide:${NC}"
echo -e "${CYAN}1. Open http://localhost:3000 in your browser${NC}"
echo -e "${CYAN}2. Go to Module Manager to create your first agent${NC}"
echo -e "${CYAN}3. Use Agent Flow to visualize your agents${NC}"
echo -e "${CYAN}4. Chat with your agents in the Chat Interface${NC}"
echo ""
echo -e "${YELLOW}📋 Logs available in:${NC}"
echo -e "   • Backend: logs/backend.log"
echo -e "   • Frontend: logs/frontend.log"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep script running and show live logs
if [ ! -z "$BACKEND_PID" ] || [ ! -z "$FRONTEND_PID" ]; then
    echo -e "${BLUE}📊 Live logs (press Ctrl+C to stop):${NC}"
    echo ""

    # Follow logs
    tail -f logs/*.log 2>/dev/null &
    TAIL_PID=$!

    # Wait for user interruption
    wait

    # Cleanup tail process
    kill $TAIL_PID 2>/dev/null || true
fi
