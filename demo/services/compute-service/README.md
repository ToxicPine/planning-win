# Compute Service

A service that runs ML computations on GPUs as part of the SplitUp Node infrastructure.

## Overview

The SplitUp Compute Service is responsible for:

1. Loading and running ML models on the GPU
2. Retrieving input tensors from decentralized storage
3. Executing computation tasks
4. Storing output tensors to decentralized storage
5. Reporting task results to the TaskListener

## Setup

1. Make sure you have Python and the required ML frameworks installed.

2. Install dependencies:

```bash
uv install
```

## Configuration

The service can be configured using environment variables:

- `SPLITUP_CLIENT_S3_API_KEY`: Your S3 API key for tensor storage
- `COMPUTE_SERVICE_PORT`: Service port (default: 8000)
- `COMPUTE_SERVICE_LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR) (default: INFO)
- `COMPUTE_SERVICE_MODEL_CACHE`: Directory for caching model weights

## Integration

The Compute Service works alongside other components in the SplitUp Node:

- **Heartbeat Service**: Maintains communication with the Oracle Committee
- **TaskListener Service**: Listens for task assignments on the blockchain
- **Pre-loading System**: Manages model weights in memory

## Running the Service

```bash
uv run main.py
```

## API Endpoints

- `GET /health`: Health check endpoint
- `POST /api/execute_task`: Execute a computation task
- `GET /api/status`: Get current GPU status and capacity
- `POST /api/preload_weights`: Preload weights for specific tasks

## Service Flow

1. TaskListener receives task assignment from blockchain
2. TaskListener forwards task to Compute Service
3. Compute Service retrieves input tensors from storage
4. Compute Service executes ML computation on GPU
5. Compute Service stores output tensors to storage
6. Results are reported back to TaskListener for blockchain submission

For a complete system overview, see the system diagrams and documentation.
