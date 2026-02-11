#!/bin/bash

# Activate virtual environment and start the server
cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Install playwright browsers if needed
if ! playwright --version &> /dev/null; then
    echo "Installing Playwright browsers..."
    playwright install chromium
fi

# Start the server
echo "Starting Invoice Processor API..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
