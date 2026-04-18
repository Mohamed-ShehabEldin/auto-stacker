#!/usr/bin/env bash

set -e

# Install all Python dependencies for auto-stacker
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "All required packages have been installed."
