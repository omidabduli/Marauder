#!/bin/bash

# MARAUDER - macOS Launcher
# This script sets up and runs the Marauder server on your Mac.

# Navigate to the script directory
cd "$(dirname "$0")"

echo "==========================================="
echo "   MARAUDER - STARTING SERVER...     "
echo "==========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Error: Python 3 is not installed."
    echo "Please install it from python.org or via Homebrew."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Checking dependencies..."
pip install --quiet -r requirements.txt

# Run the server
echo "Server is starting..."
echo "Open http://127.0.0.1:5005 in your browser"
echo "==========================================="
python server.py
