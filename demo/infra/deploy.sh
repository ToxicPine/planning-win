#!/bin/bash

# Exit on error
set -e

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing API dependencies..."
cd api
pip install -r requirements.txt
cd ..

# Deploy using Zappa
echo "Deploying API..."
cd api
zappa deploy dev
cd ..

echo "Deployment complete!"
echo "Please check the Zappa output for the API endpoint URL" 