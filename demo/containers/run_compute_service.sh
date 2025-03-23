#!/bin/bash
# Load environment variables from .env file
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi

docker-compose -f compute-node.yml up