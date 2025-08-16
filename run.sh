#!/bin/bash

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup first..."
    ./setup.sh
    if [ $? -ne 0 ]; then
        exit 1
    fi
fi

echo "Starting Desktop Utility GUI..."
source venv/bin/activate && python main.py