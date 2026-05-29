#!/bin/bash

# --- Check if Ollama is running ---
if ! pgrep -x "ollama" > /dev/null; then
    echo "Iniciando Ollama..."
    ollama serve > /home/rumpel/tabris/ollama.log 2>&1 &
    sleep 3
else
    echo "Ollama ya esta corriendo."
fi

# --- Check if venv is active and activate if needed ---
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activando entorno virtual..."
    source /home/rumpel/tabris/venv/bin/activate
else
    echo "Entorno virtual ya esta activo."
fi

# --- Start Tabris ---
echo "Iniciando Tabris..."
cd /home/rumpel/tabris
python tabris.py
