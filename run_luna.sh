#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate the virtual environment
source venv/bin/activate

# Run the main application
python main.py
