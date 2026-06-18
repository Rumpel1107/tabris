#!/bin/bash

# --- Check if Ollama service is running ---
if ! systemctl is-active --quiet ollama; then
    echo "Starting Ollama..."
    sudo systemctl start ollama
    sleep 3
else
    echo "Ollama is already running."
fi

# --- Check if venv is active and activate if needed ---
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source ~/Projects/tabris/venv/bin/activate
else
    echo "Virtual environment is already active."
fi

# --- Start Tabris ---
echo "Starting Tabris..."
cd ~/Projects/tabris
python main.py
