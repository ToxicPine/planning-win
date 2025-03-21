# SplitUp Node: Component Orchestration Guide

This document explains how the SplitUp Node components work together to provide reliable ML computation services with proper liveness reporting to the Oracle Committee. It should be read alongside the [Oracle Committee Communication Protocol Specification](../heartbeat/oracle_server.md) which details the specific data formats and APIs.

## System Overview

A SplitUp Node consists of two containerized services:

1. **TypeScript Heartbeat Service**: Maintains communication with the Oracle Committee
2. **Python Compute Service**: Performs ML computations on the GPU

These services work together to ensure both reliable computation and proper network status reporting.

```mermaid
graph TD
    Blockchain[Solana Blockchain] <--"listens for tasks, publishes result when complete"--> TL
    OracleCommittee[Oracle Committee] --"tells chain which node to pick"--> Blockchain

    subgraph "SplitUp Node (Docker Compose)"
        HS[Heartbeat Service]
        TL[TaskListener Service] <--> CS[Compute Service]
        HS <--> CS
    end

    HS --> OracleCommittee

    subgraph "GPU Resources"
        CS --> GPU[Local GPU]
    end

    subgraph "External Services"
        CS <--> Storage[Decentralized Storage]
    end
```

## Service Responsibilities

### TypeScript Heartbeat Service

- Maintains cryptographic identity (Solana keypair)
- Sends regular heartbeats to the Oracle Committee
- Reports node capacity status
- Ensures node liveness is properly tracked

### TypeScript TaskListener Service

- Listens for task assignment events on the Solana blockchain
- Forwards tasks to the Compute Service
- Submits task completion transactions back to the blockchain
- Tracks pending task executions

### Python Compute Service

- Loads and runs ML models on the GPU
- Retrieves input tensors from decentralized storage
- Executes computation tasks
- Stores output tensors to decentralized storage
- Reports task results to the TaskListener

## Docker Compose Configuration

Below is the updated Docker Compose configuration that orchestrates these services:

```yaml
version: "3"

services:
  heartbeat-service:
    build: ./heartbeat-service
    ports:
      - "3000:3000" # Heartbeat service API port
    volumes:
      - ./keys:/app/keys # Mount volume for Solana keys
    environment:
      - NODE_ENV=production
      - HEARTBEAT_INTERVAL_MS=30000
    restart: always
    depends_on:
      - compute-service

  task-listener:
    build: ./task-listener
    ports:
      - "3001:3001" # TaskListener API port
    volumes:
      - ./keys:/app/keys # Same keys as heartbeat service
    environment:
      - NODE_ENV=production
      - SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
      - SPLITUP_PROGRAM_ID=YOUR_PROGRAM_ID_HERE
    restart: always
    depends_on:
      - compute-service

  compute-service:
    build: ./compute-service
    ports:
      - "8000:8000" # Compute service API port
    volumes:
      - ./model-cache:/app/model-cache # Cache for model weights
      - ./tensor-cache:/app/tensor-cache # Cache for tensors
    environment:
      - ENVIRONMENT=production
      - STORAGE_API_URL=https://URL_HERE.TLD
    restart: always
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Communication Flow

### Service Initialization

```mermaid
sequenceDiagram
    participant TS as Heartbeat Service
    participant TL as TaskListener Service
    participant PY as Compute Service
    participant OC as Oracle Committee

    Note over TS,PY: Docker Compose starts services
    PY->>PY: Initialize and check GPU availability
    TS->>TS: Load Solana keypair
    TL->>TL: Initialize blockchain listeners
    TS->>TS: Start API server
    TL->>TL: Start API server
    PY->>TS: POST /api/compute-status (initial status)
    TS->>OC: POST /api/heartbeat (first heartbeat)

    Note over TS,PY: Operational state reached
```

### Regular Status Updates

```mermaid
sequenceDiagram
    participant PY as Compute Service
    participant TS as Heartbeat Service
    participant TL as TaskListener Service
    participant OC as Oracle Committee

    loop Every 30 seconds
        PY->>PY: Check current capacity
        PY->>PY: Create ComputeStatus object
        PY->>TS: POST /api/compute-status

        TS->>TS: Update internal node status
        TS->>TS: Create and sign HeartbeatData
        TS->>OC: POST /api/heartbeat

        TL->>TL: Monitor blockchain for tasks
    end
```

### Task Completion

This flow is described in detail within [`task_completion.md`](./task_completion.md)
