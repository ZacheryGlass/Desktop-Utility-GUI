#!/bin/bash

echo "Desktop Utility GUI Setup"
echo "========================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv venv

if [ ! -d "venv" ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

echo
echo "Activating virtual environment..."
source venv/bin/activate

echo
echo "Upgrading pip..."
python -m pip install --upgrade pip

echo
echo "Installing required packages..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo
    echo "Error: Failed to install some packages"
    echo "Please check the error messages above"
    exit 1
fi

echo
echo "========================="
echo "Setup completed successfully!"
echo
echo "To run the application:"
echo "  1. Run: source venv/bin/activate"
echo "  2. Run: python main.py"
echo
echo "Or simply run: ./run.sh"
echo "========================="