#!/bin/bash

echo "==================================================="
echo "🌍 AracimSaglam Global Access Launcher"
echo "==================================================="

# Check for cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared is not installed."
    echo "Please install it: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
    exit 1
fi

echo ""
echo "1. Starting Flask App..."
# Start in background
python3 run_app.py > /dev/null 2>&1 &
APP_PID=$!

echo ""
echo "2. Waiting for server to initialize..."
sleep 5

echo ""
echo "3. Starting Cloudflare Tunnel..."
echo "---------------------------------------------------"
echo "🔗 Your PUBLIC URL is creating... (look for *.trycloudflare.com)"
echo "---------------------------------------------------"
echo ""

# Start tunnel
cloudflared tunnel --url http://localhost:5000

# Cleanup on exit
kill $APP_PID
