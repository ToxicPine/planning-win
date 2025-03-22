# Heartbeat Oracle Server

This is the Oracle Committee server component that receives and verifies heartbeats from compute nodes.

## Setup

1. Make sure you have Deno installed. If not, follow the [official installation guide](https://docs.deno.com/runtime/manual/getting_started/installation).

2. Install dependencies:

```
deno cache main.ts
```

## Configuration

The server can be configured using environment variables with the prefix `SPLITUP_ORACLE_`:

- `SPLITUP_ORACLE_SERVICE_PORT`: Server port (default: 8000)
- `SPLITUP_ORACLE_SERVICE_HOST`: Server host (default: localhost)
- `SPLITUP_ORACLE_SERVICE_PRIVATE_KEY`: Oracle service private key (no default)
- `SPLITUP_ORACLE_COMMITTEE_ADDRESSES`: Comma-separated list of oracle committee addresses (no default)
- `SPLITUP_ORACLE_SERVICE_OFFLINE_THRESHOLD_MS`: Threshold in milliseconds to consider a node offline (default: 90000)
- `SPLITUP_ORACLE_SERVICE_CLEANUP_INTERVAL_MS`: Interval in milliseconds for cleaning up offline nodes (default: 30000)
- `SPLITUP_ORACLE_SERVICE_LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) (default: INFO)
- `SPLITUP_ORACLE_SERVICE_LOG_FORMAT`: Whether to format logs as JSON (default: false)

## Running the Server

```bash
deno task start
```

Or with explicit permissions:

```bash
deno run --allow-net --allow-env main.ts
```

## API Endpoints

- `GET /`: Welcome message
- `GET /api/stats`: Get system-wide statistics
- `GET /api/nodes`: Get status of all nodes
- `POST /api/heartbeat`: Receive heartbeats from nodes
- `GET /health`: Health check endpoint
