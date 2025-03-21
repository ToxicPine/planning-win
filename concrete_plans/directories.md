# SplitUp Project Architecture: Detailed Directory Structure and Rationale

## Overview

This structure maintains clear separation of concerns while enabling the necessary interactions between components.

Note that this architecture is illustrative and should not be taken as final. Depending on the TypeScript frameworks used and other implementation details, the requirements may differ. The goal is to provide a starting point that captures the essential components and their relationships.

## High-Level Directory Structure

```
splitup/
├── apps/                   # User-facing applications
├── packages/               # Shared libraries
├── services/               # Backend services (containerized)
├── cli/                    # Command-line tools
├── contracts/              # Solana smart contracts
└── scripts/                # Project-wide scripts
```

## Detailed Project Structure

```
splitup/
├── apps/
│   └── mnist-demo/                     # Next.js MNIST demo app
│       ├── src/
│       │   ├── app/                    # Next.js app router
│       │   ├── components/             # React components
│       │   └── lib/                    # Client SDK integration
│       ├── package.json
│       └── tsconfig.json
│
├── packages/
│   ├── common-ts/                      # Shared TypeScript code
│   │   ├── src/
│   │   │   ├── types/                  # Protocol and API types
│   │   │   │   ├── heartbeat.ts        # Heartbeat protocol types
│   │   │   │   ├── task.ts             # Task execution types
│   │   │   │   ├── tensor.ts           # Tensor specification types
│   │   │   │   └── oracle.ts           # Oracle consensus types
│   │   │   ├── blockchain/             # Solana client utilities
│   │   │   └── crypto/                 # Signature generation/verification
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── common-py/                      # Shared Python code
│       ├── splitup_common/
│       │   ├── __init__.py
│       │   ├── types.py                # Protocol and API types
│       │   ├── tensor.py               # Tensor handling utilities
│       │   ├── storage.py              # Storage client abstraction
│       │   └── schemas/                # Shared Pydantic schemas
│       │       ├── __init__.py
│       │       ├── config.py           # Configuration schemas
│       │       ├── tasks.py            # Task execution schemas
│       │       ├── status.py           # Status reporting schemas
│       │       └── cache.py            # Cache management schemas
│       ├── Pipfile
│       └── Pipfile.lock
│
├── services/
│   ├── compute-service/                # Python ML computation engine
│   │   ├── splitup_compute/
│   │   │   ├── __init__.py
│   │   │   ├── engine/                 # ML execution engine
│   │   │   │   ├── executor.py         # Task execution logic
│   │   │   │   └── model.py            # Model loading/execution
│   │   │   ├── api/                    # FastAPI service
│   │   │   │   ├── server.py           # API server setup
│   │   │   │   ├── tasks.py            # Task execution endpoints
│   │   │   │   └── status.py           # Status reporting endpoints
│   │   │   ├── cache/                  # Weight preloading/caching
│   │   │   │   ├── manager.py          # Cache management
│   │   │   │   └── preloader.py        # Weight prefetching
│   │   │   └── storage/                # Storage integration
│   │   │       ├── client.py           # Storage client implementation
│   │   │       └── tensor.py           # Tensor serialization
│   │   ├── Pipfile
│   │   ├── Pipfile.lock
│   │   └── Dockerfile
│   │
│   ├── heartbeat-service/              # TypeScript heartbeat service
│   │   ├── src/
│   │   │   ├── trpc/                   # tRPC router definition
│   │   │   │   ├── router.ts           # API route definitions
│   │   │   │   └── server.ts           # tRPC server setup
│   │   │   ├── heartbeat/              # Heartbeat functionality
│   │   │   │   ├── generator.ts        # Heartbeat data generation
│   │   │   │   └── sender.ts           # Oracle communication
│   │   │   ├── compute/                # Compute service client
│   │   │   │   └── status.ts           # Compute status tracking
│   │   │   └── crypto/                 # Cryptographic operations
│   │   │       └── signature.ts        # Signature generation
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── Dockerfile
│   │
│   ├── task-listener/                  # TypeScript blockchain listener
│   │   ├── src/
│   │   │   ├── trpc/                   # tRPC router definition
│   │   │   │   ├── router.ts           # Task API definitions
│   │   │   │   └── server.ts           # tRPC server setup
│   │   │   ├── listener/               # Blockchain listener
│   │   │   │   ├── events.ts           # Task event handlers
│   │   │   │   └── subscription.ts     # Blockchain subscriptions
│   │   │   └── tasks/                  # Task management
│   │   │       ├── queue.ts            # Task queue management
│   │   │       └── compute.ts          # Compute service client
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── Dockerfile
│   │
│   └── oracle-committee/               # TypeScript oracle implementation
│       ├── src/
│       │   ├── trpc/                   # tRPC API definition
│       │   ├── consensus/              # BFT consensus protocol
│       │   │   ├── protocol.ts         # Consensus algorithm
│       │   │   └── voting.ts           # Vote collection/counting
│       │   ├── liveness/               # Node liveness tracking
│       │   │   ├── table.ts            # Liveness state management
│       │   │   └── heartbeats.ts       # Heartbeat processing
│       │   └── selection/              # Node selection
│       │       ├── algorithm.ts        # Selection algorithm
│       │       └── vrf.ts              # Verifiable random functions
│       ├── package.json
│       ├── tsconfig.json
│       └── Dockerfile
│
├── cli/
│   ├── node-cli/                       # Python node operator CLI
│   │   ├── splitup_node/
│   │   │   ├── __init__.py
│   │   │   ├── commands/               # Click command groups
│   │   │   │   ├── register.py         # Node registration
│   │   │   │   ├── configure.py        # Service configuration
│   │   │   │   └── status.py           # Status commands
│   │   │   └── config/                 # Configuration management
│   │   │       ├── schema.py           # Config validation
│   │   │       └── storage.py          # Config persistence
│   │   ├── Pipfile
│   │   └── Pipfile.lock
│   │
│   ├── model-deploy-cli/               # Python model deployment CLI
│   │   ├── splitup_deploy/
│   │   │   ├── __init__.py
│   │   │   ├── commands/               # Click command groups
│   │   │   │   ├── register.py         # Model registration
│   │   │   │   ├── partition.py        # Model partitioning
│   │   │   │   └── inspect.py          # Model inspection
│   │   │   ├── partition/              # Partitioning logic
│   │   │   │   ├── auto.py             # Automatic partitioning
│   │   │   │   ├── memory.py           # Memory profiling
│   │   │   │   └── graph.py            # DAG creation/manipulation
│   │   │   └── tensor/                 # Tensor context
│   │   │       ├── context.py          # Tensor context creation 
│   │   │       └── profiling.py        # Memory usage profiling
│   │   ├── Pipfile
│   │   └── Pipfile.lock
│   │
│   └── admin-cli/                      # TypeScript admin CLI
│       ├── src/
│       │   ├── commands/               # Command implementation
│       │   └── utils/                  # CLI utilities
│       ├── package.json
│       └── tsconfig.json
│
├── contracts/                          # Solana smart contracts
│   ├── programs/
│   │   ├── model-registry/             # Model registry
│   │   ├── task-registry/              # Task registry
│   │   ├── node-registry/              # Node registry
│   │   ├── model-execution/            # Execution contract
│   │   ├── verification/               # PoSP verification
│   │   └── staking/                    # Staking contract
│   ├── Anchor.toml
│   └── Cargo.toml
│
├── docker-compose.yml                  # Node deployment setup
├── pnpm-workspace.yaml                 # pnpm workspace config
├── package.json                        # Root package.json
└── README.md
```

## Component Functions and Rationale

### 1. Node Software Stack Components

Based on the documentation, the SplitUp Node consists of three main containerized services that work together:

#### 1.1 Compute Service (Python)

**Function:** Core ML execution engine that runs on the GPU.

**Responsibilities:**
- Execute ML computation tasks on GPU hardware
- Manage model weight preloading and caching
- Retrieve input tensors from storage
- Store output tensors to storage
- Report execution results and status
- Centralize configuration management for node components

**Key Components:**
- **Engine Module:** Handles the actual ML computation using TinyGrad or similar framework
- **Cache Module:** Manages the preloading of weights for specialized tasks (absorbing the preloading system functionality)
- **API Module:** Provides FastAPI endpoints for task execution, status reporting, and configuration management
- **Storage Module:** Handles tensor retrieval and storage
- **Config Module:** Centralized configuration management with persistence

**Rationale:** This service needs direct access to GPU resources and handles the computationally intensive operations. Python is chosen for its extensive ML libraries and GPU integration capabilities. The service also acts as the central configuration store, with APIs allowing dynamic updates.

#### 1.2 Heartbeat Service (TypeScript)

**Function:** Maintains liveness signaling with the Oracle Committee.

**Responsibilities:**
- Maintain cryptographic identity (Solana keypair)
- Send regular signed heartbeats to Oracle Committee
- Report node capacity and status
- Poll Compute Service for resource availability

**Key Components:**
- **Heartbeat Module:** Handles creation and sending of heartbeats
- **Crypto Module:** Manages cryptographic operations for signing
- **Compute Client:** Communicates with Compute Service for status updates

**Rationale:** This service handles the cryptographic operations and blockchain identity. TypeScript offers strong typing for protocol definitions and simplifies integration with the Oracle Committee.

#### 1.3 Task Listener Service (TypeScript)

**Function:** Monitors the blockchain for task assignments and orchestrates task execution.

**Responsibilities:**
- Listen for task assignments on the blockchain
- Forward tasks to the Compute Service
- Report task completion back to the blockchain
- Track pending task executions

**Key Components:**
- **Listener Module:** Subscribes to blockchain events
- **Tasks Module:** Manages task queue and lifecycle
- **Compute Client:** Communicates with Compute Service for task execution

**Rationale:** This service bridges the blockchain and the Compute Service. TypeScript provides strong typing for blockchain interactions and protocol definitions.

### 2. CLI Tools

#### 2.1 Node CLI (Python with Click)

**Function:** Provides node operators with tools to configure and manage their SplitUp Node.

**Responsibilities:**
- Register node with the network
- Configure node specialization
- Manage Solana keypair
- Control service startup/shutdown
- Configure Docker Compose deployment

**Key Components:**
- **Commands Module:** Click command implementations
- **Config Module:** Configuration management and validation
- **API Client:** Type-safe client for compute service API using shared schemas

**Rationale:** This CLI provides a unified interface for node management, using both configuration files and direct API communication with running services for dynamic configuration updates.

#### 2.2 Model Deploy CLI (Python with Click)

**Function:** Enables model developers to partition and register models with the SplitUp network.

**Responsibilities:**
- Analyze ML models for partitioning
- Create task definitions with appropriate interfaces
- Upload weight files to decentralized storage
- Register tasks and models with the blockchain

**Rationale:** Separation from services allows model developers to use this tool without needing to run a full node. Python is selected for its ML ecosystem integration.

### 3. Communication Patterns

#### 3.1 Inter-Service Communication

The services within a SplitUp Node communicate as follows:

1. **Compute Service ↔ Heartbeat Service:** 
   - Protocol: REST API (FastAPI in Python)
   - Direction: Heartbeat Service polls Compute Service for status
   - Endpoint: `/api/compute-status` as defined in heartbeat/oracle_server.md
   - Schema: Shared via common-ts types

2. **Compute Service ↔ Task Listener:**
   - Protocol: REST API (FastAPI in Python)
   - Direction: Task Listener forwards tasks to Compute Service
   - Endpoint: `/api/task` as defined in compute_client/task_completion.md

3. **CLI Tools ↔ Compute Service:**
   - Protocol: REST API (FastAPI in Python)
   - Direction: CLI tools communicate with Compute Service for runtime configuration
   - File-based: CLI tools also manage configuration files for initial setup and persistence
   - Endpoints: 
     - `/api/config` for configuration management
     - `/api/status` for service status queries
   - Schema: Shared Pydantic models from common-py package

**Benefits of Shared Schemas:**
- Type-safety across components
- Consistent validation rules
- Automatic documentation generation
- Single source of truth for API contracts

**Rationale:** This hybrid configuration approach provides flexibility for both initial setup and runtime updates. Using shared Pydantic schemas between the CLI and compute service ensures consistent API contracts and type-safety.

#### 3.2 External Communication

1. **Heartbeat Service → Oracle Committee:**
   - Protocol: HTTPS with signed payloads
   - Endpoint: `/api/heartbeat` on Oracle Committee
   - Frequency: Every 30 seconds

2. **Task Listener → Blockchain:**
   - Protocol: Solana RPC
   - Actions: Monitor events, submit transactions
   - Frequency: Continuous subscription + on-demand

3. **Compute Service ↔ Storage:**
   - Protocol: Decentralized storage API (possibly IPFS or custom)
   - Operations: Fetch weights, store/retrieve tensors

**Rationale:** These communication patterns follow the design in the protocol documentation, with clear separation between fast-changing node status (handled by Oracle Committee) and permanent on-chain state (managed by smart contracts).

### 4. Docker Compose Integration

The `docker-compose.yml` bundles the three services that form a SplitUp Node:

```yaml
version: "3"

services:
  heartbeat-service:
    build: ./services/heartbeat-service
    ports:
      - "3000:3000"
    volumes:
      - ./keys:/app/keys # Shared volume for Solana keys
      - ./config:/app/config # Shared initial configuration
    environment:
      - NODE_ENV=production
      - HEARTBEAT_INTERVAL_MS=30000
    restart: always

  task-listener:
    build: ./services/task-listener
    ports:
      - "3001:3001"
    volumes:
      - ./keys:/app/keys # Same keys as heartbeat service
      - ./config:/app/config # Shared initial configuration
    environment:
      - NODE_ENV=production
      - SOLANA_RPC_URL=${SOLANA_RPC_URL}
    restart: always

  compute-service:
    build: ./services/compute-service
    ports:
      - "8000:8000"
    volumes:
      - ./model-cache:/app/model-cache # Cache for model weights
      - ./tensor-cache:/app/tensor-cache # Cache for tensors
      - ./config:/app/config # Configuration files
    environment:
      - ENVIRONMENT=production
      - STORAGE_API_URL=${STORAGE_API_URL}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**Rationale:**
- The CLI tools can both modify configuration files for initial setup and communicate with running services via API for runtime updates
- The Compute Service acts as the central configuration manager with persistence capabilities
- All services have access to initial configuration files, but runtime updates are coordinated through the Compute Service
- Explicit environment variables for inter-service communication ensure proper connectivity

## Justification Based on Documentation

### 1. System Flow Alignment

The proposed structure directly maps to the system flows described in the documentation:

1. **Model Deployment Flow** (red in diagram):
   - Handled by the Model Deploy CLI
   - Separate from the node services as it's a developer tool

2. **Node Registration Flow** (green in diagram):
   - Managed by Node CLI for initial setup
   - Configuration created by CLI is used by services

3. **Task Execution Flow** (blue in diagram):
   - Task Listener monitors blockchain for assignments
   - Compute Service performs the actual execution
   - Results reported back via Task Listener

4. **Verification Flow** (purple in diagram):
   - Leverages same components as task execution
   - Probabilistic verification via PoSP (8% of tasks)

5. **Heartbeat/Liveness Flow** (orange in diagram):
   - Heartbeat Service maintains communication with Oracle
   - Status information collected from Compute Service

### 2. Protocol Implementation

The directory structure is designed to cleanly implement the protocols defined in:

1. **Task Completion Protocol** (compute_client/task_completion.md):
   - Task Listener and Compute Service implement this flow
   - API endpoints match the specification

2. **Oracle Committee Communication** (heartbeat/oracle_server.md):
   - Heartbeat Service implements the node-to-oracle protocol
   - Data types match the specification

3. **Oracle Consensus Protocol** (heartbeat_oracle/index.md):
   - Oracle Committee service implements BFT consensus
   - Node selection algorithms follow specification

4. **Model Deployment** (model_deployment/index.md):
   - Model Deploy CLI implements partitioning workflow
   - Structure preserves DAG integrity

5. **Proof of Sampling Protocol** (smart_contracts/proof_of_sampling.md):
   - Verification contract implements 8% verification rate
   - Economic incentives preserved in implementation

### 3. Component Separation

The clear separation between CLI tools and services reflects the different roles and lifecycles:

1. **CLI Tools**:
   - Used by humans for setup and configuration
   - Run occasionally and manually
   - Primarily interact with blockchain and storage

2. **Services**:
   - Run continuously without user intervention
   - Communicate with other services via well-defined APIs
   - Perform automated functions based on events

This separation enables clean configuration management - CLIs create configs, services consume them.

## Conclusion

This structure provides a comprehensive implementation of the SplitUp system as described in the documentation. By clearly separating concerns between services and CLI tools, and establishing well-defined communication patterns, the architecture enables:

1. **Clean component separation** with well-defined responsibilities
2. **Type-safe communication** between components using tRPC, FastAPI, and shared schemas
3. **Consistent data schemas** shared via common packages
4. **Independent development** of different system components
5. **Simplified deployment** via Docker Compose
6. **Flexible configuration management** that supports both file-based and API-based approaches
7. **Schema-driven development** with centralized definitions for API contracts

The preloading system has been absorbed by the Compute Service's cache module. Configuration management is centralized in the Compute Service with a hybrid approach allowing both static file-based configuration and dynamic API-based updates. Schema sharing between Python components ensures consistent and type-safe communication between the CLI tools and services.
