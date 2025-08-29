#!/bin/bash

echo "Setting up ZVEI/CCIR SDR Monitor on Raspberry Pi"

# Update system
sudo apt-get update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y python3-pip python3-dev librtlsdr-dev rtl-sdr python3-venv

# Install Python packages from apt where available
echo "Installing Python packages..."
sudo apt-get install -y python3-numpy python3-scipy python3-yaml

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate and install remaining packages
source venv/bin/activate
pip install pyrtlsdr pyyaml

echo "Testing RTL-SDR..."
rtl_test -t

echo "Setup complete!"
echo ""
echo "To run the monitor:"
echo "  source venv/bin/activate"
echo "  python zvei_monitor.py"
echo ""
echo "Or run directly:"
echo "  ./run_monitor.sh"