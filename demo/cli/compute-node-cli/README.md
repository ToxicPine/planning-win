# Node Management CLI

A command-line interface for registering and managing SplitUp compute nodes in the decentralized ML computation network.

## Overview

The SplitUp Node Management CLI enables node operators to:

1. Register compute nodes on the SplitUp network
2. Specialize in specific ML model tasks
3. Stake USDC as security collateral
4. Configure node settings and weight management
5. Start and monitor node services

## Setup

1. Make sure you have Python and the required dependencies installed.

2. Install the CLI:

```bash
uv install splitup-node
```

## Configuration

The CLI can be configured using environment variables with the prefix `SPLITUP_CLIENT_`:

- `SPLITUP_CLIENT_S3_API_KEY`: Your S3 API key for tensor and weight storage
- `SPLITUP_CLIENT_SOLANA_PRIVATE_KEY`: Base58 Solana private key.
- `SPLITUP_CLIENT_LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR) (default: INFO)
- `SPLITUP_CLIENT_MODEL_CACHE_DIR`: Directory for caching model weights

## Usage

### Register a Node

```bash
# Register a node with the SplitUp network
splitup-node register --stake-amount 1000
```

### Specialize in Specific Tasks

```bash
# Declare which tasks this node will specialize in
splitup-node specialize --model-id llama-70b --tasks 1,2,3
```

### Preload Model Weights

```bash
# Preload weights for better performance
splitup-node preload --model-id llama-70b --tasks 1,2,3
```

### Start Node Services

```bash
# Start all node services (heartbeat, task listener, compute)
splitup-node start
```

### Check Node Status

```bash
# Get current node status
splitup-node status
```

## Node Components

The CLI manages the following containerized services:

1. **Heartbeat Service**: Maintains communication with the Oracle Committee
2. **TaskListener Service**: Listens for task assignments on the blockchain
3. **Compute Service**: Performs ML computations on the GPU

## Security and Staking

Nodes must stake USDC as collateral to participate in the network.

The staked amount ensures security within the verification system, incentivizing honest node behavior through rewards and deterring dishonesty with potential stake loss.

For more detailed information about the node registration process and economic model, please refer to the project documentation.