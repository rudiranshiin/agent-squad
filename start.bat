@echo off
setlocal enabledelayedexpansion

REM 🚀 Enhanced Agentic Framework - Windows Startup Script
REM This script starts both the backend and frontend development servers

title Enhanced Agentic Framework 2.0

echo.
echo 🚀 Enhanced Agentic Framework 2.0
echo Starting development environment...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm is not installed
    echo Please install Node.js with npm
    pause
    exit /b 1
)

echo ✅ All dependencies found
echo.

REM Create logs directory
if not exist "logs" mkdir logs

REM Install Python dependencies if needed
echo 📦 Checking Python dependencies...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Warning: Some Python dependencies may not have installed properly
) else (
    echo ✅ Python dependencies ready
)

REM Install frontend dependencies if needed
if not exist "frontend\node_modules" (
    echo 📦 Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
    if errorlevel 1 (
        echo ❌ Failed to install frontend dependencies
        pause
        exit /b 1
    )
    echo ✅ Frontend dependencies installed
) else (
    echo ✅ Frontend dependencies already installed
)

echo.
echo 🎯 Starting services...
echo.

REM Start backend in a new window
echo 🐍 Starting backend server (Port 8000)...
start "Agentic Framework Backend" /min cmd /k "uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
echo ⚛️ Starting frontend server (Port 3000)...
start "Agentic Framework Frontend" /min cmd /k "cd frontend && npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo 🎉 Services Starting...
echo.
echo ✅ Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo ✅ Frontend UI: http://localhost:3000
echo.
echo 🎯 Quick Start Guide:
echo 1. Open http://localhost:3000 in your browser
echo 2. Go to Module Manager to create your first agent
echo 3. Use Agent Flow to visualize your agents
echo 4. Chat with your agents in the Chat Interface
echo.
echo 📋 Both services are running in separate windows
echo 💡 Close the terminal windows to stop the services
echo.

REM Wait for user to see the output before opening browser
timeout /t 3 /nobreak >nul

REM Open the frontend in default browser
echo 🌐 Opening frontend in your default browser...
start http://localhost:3000

echo.
echo ✨ Setup complete! You can now use the Enhanced Agentic Framework.
echo.
pause
