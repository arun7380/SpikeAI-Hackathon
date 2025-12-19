#!/bin/bash

# 1. Configuration & Path Setup
PROJECT_DIR="/d/Career/SpikeAI-Hackathon"
VENV_DIR="$PROJECT_DIR/.venv"
TEMP_DIR="/d/Career/pip_temp"

echo "--- Starting Spike AI Deployment ---"

# 2. Create a custom temp directory on D: drive to avoid 'No Space Left' on C:
if [ ! -d "$TEMP_DIR" ]; then
    mkdir -p "$TEMP_DIR"
    echo "[INFO] Created temp directory on D: drive."
fi

# Set global environment variables for this session
export TMPDIR="$TEMP_DIR"
export PYTHONPATH=$PYTHONPATH:.
export GOOGLE_APPLICATION_CREDENTIALS="$PROJECT_DIR/credentials.json"

# 3. Virtual Environment Setup
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating virtual environment..."
    python -m venv "$VENV_DIR" --without-pip
    source "$VENV_DIR/Scripts/activate"
    
    echo "[INFO] Installing pip manually to D: drive..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py --no-cache-dir
    rm get-pip.py
else
    source "$VENV_DIR/Scripts/activate"
    echo "[INFO] Virtual environment activated."
fi

# 4. Dependency Installation
echo "[INFO] Installing requirements (Redirecting cache to D:)..."
pip install -r requirements.txt --cache-dir="$TEMP_DIR" --no-cache-dir

# 5. Start the Server
echo "[SUCCESS] Environment ready. Launching FastAPI server on port 8080..."
python -m api.server