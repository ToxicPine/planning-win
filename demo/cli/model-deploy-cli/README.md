# Model Deployment CLI

A command-line tool for automatic partitioning and registration of large ML models in the SplitUp network.

## Overview

The SplitUp Model Deployment CLI enables model developers to:

- Register large models that would not fit on single consumer GPUs
- Automatically partition models into smaller tasks based on VRAM constraints
- Define explicit tensor interfaces between tasks
- Register model weights to decentralized storage
- Create an immutable model DAG structure on the blockchain

## Setup

1. Make sure you have Python and uv installed.

2. Install the CLI:

```bash
uv install splitup-deploy
```

## Configuration

The CLI uses environment variables with the prefix `SPLITUP_CLIENT_`:

- `SPLITUP_CLIENT_S3_API_KEY`: Your S3 API key for model weight storage
- `SPLITUP_CLIENT_SOLANA_PRIVATE_KEY`: Base58 Solana private key.
- Other configuration options will be documented as they are implemented

## Usage

Based on the information from the documentation:

```bash
# Register a model with target VRAM constraint
splitup-deploy register \
  --model llama-70b.pkl \
  --target-vram 12 \
  --name "LLaMA 70B" \
  --description "Meta's 70B Parameter LLM" \
  --framework tinygrad

# Get model information after registration
splitup-deploy info <model-id>

# Test model execution on the network
splitup-deploy test-execution <model-id> --input-file prompt.json
```

## Deployment Process

The deployment process consists of:

1. **Model Loading and Analysis**: Parsing the computational graph
2. **Automatic Partitioning**: Creating split points based on VRAM constraints
3. **Task Registration**: Uploading task definitions and weights to storage
4. **Model Registration**: Registering the complete model structure on the blockchain

For more detailed information about the partitioning algorithms and system architecture, please refer to the project documentation.
