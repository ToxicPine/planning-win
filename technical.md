# SplitUp: Technical Specification Document

## 1. Executive Summary

SplitUp is a decentralized GPU computation platform that enables running large-scale machine learning models across consumer-grade hardware. It addresses two critical challenges in decentralized ML:

1. **VRAM Capacity Limitation**: Modern ML models require more VRAM than available on consumer GPUs. SplitUp automatically partitions models into smaller tasks that can be distributed across multiple GPUs.

2. **Verification Overhead**: Traditional verification methods impose >100% overhead. SplitUp implements the Proof of Sampling Protocol (PoSP) with only 5-10% verification overhead while maintaining security guarantees.

Built on EigenTensor's memory-safe computational format and Solana's efficient smart contract platform, SplitUp enables true democratization of ML computation through an optimized DAG-based execution engine.

### Resources

[Proof of Sampling](https://arxiv.org/pdf/2405.00295) Paper, Consensus We Will Use.

[EigenTensor](https://github.com/ToxicPine/eigentensor/blob/main/README.md), Our Basis ML Computations.

## 2. System Architecture Overview

### Core Architecture Components

SplitUp's architecture consists of four primary layers:

1. **Solana Contract Layer**: Handles task registration, node management, execution orchestration, and economic incentives
2. **Node Execution Layer**: Manages specialized task execution, weight pre-loading, and result verification
3. **Storage Layer**: Provides decentralized storage for model definitions, weights, and tensor data
4. **Client Interface Layer**: Enables model deployment, task submission, and result retrieval

### Fundamental Concepts

- **Model as DAG**: Models represented as Directed Acyclic Graphs of computational tasks
- **Task as Pure Function**: Each task has explicit input and output tensor interfaces
- **Pre-loading**: Nodes specialize in specific tasks by pre-loading weights
- **Multi-Task Assignment**: High-capacity nodes can handle multiple adjacent tasks
- **PoSP Verification**: Economically-secured verification with minimal overhead

## 3. Solana Contract Components

### Model Registry

Maintains the registry of model definitions with their DAG structures:

- Stores model metadata and complete DAG structure
- Manages task specifications and interface definitions
- Tracks relationships between tasks and tensor flows
- Provides validation of DAG structure

### Task Registry

Defines individual computational tasks within models:

- Specifies input and output tensor interfaces
- Sets VRAM and computational requirements
- Tracks weight file locations and specifications
- Maintains task execution statistics

### Node Registry

Manages compute node participation in the network:

- Tracks node capabilities, specializations, and stake
- Monitors node liveness and performance metrics
- Provides node selection interfaces for task assignment

### Model Execution

Orchestrates the execution of complete models:

- Assigns tasks to nodes based on optimal allocation
- Tracks execution state and dependency satisfaction
- Handles result aggregation and verification

### Verification

Implements the PoSP security protocol:

- Determines verification tasks using VRF
- Manages validator selection and validation results
- Handles dispute resolution for mismatched results
- Enforces economic security parameters

### Staking

Manages economic security deposits:

- Handles stake deposits and withdrawals
- Implements slashing conditions for protocol violations
- Distributes rewards for honest participation
- Manages lockup periods and stake requirements

### Oracle Committee

Coordinates critical security decisions:

- Monitors node liveness through heartbeat consensus
- Provides BFT consensus for critical decisions
- Validates fair node selection through VRF
- Arbitrates disputes in verification process

## 4. Node Software Components

### Task Executor

Processes assigned computational tasks:

- Uses TinyGrad for GPU execution
  - Tasks are compiled to device-optimized machine code
- Provides interface of tensor input and output
- Executes only specific task types based on specialization

### Pre-loading System

Manages task weight availability:

- Downloads and verifies weight files for specialized tasks
- Pre-loads weights into GPU memory for instant execution
- Optimizes memory utilization for multi-task handling
- Manages cache priorities based on task frequency

### Heartbeat Service

Maintains node liveness signaling:

- Sends regular heartbeats to Oracle Committee
- Monitors health of local GPU resources
- Handles graceful shutdown and recovery

### Specialization Manager (Advanced, Optional)

Handles node specialization strategy:

- Determines optimal task specializations
- Manages weight downloading and pre-loading
- Adjusts specialization based on market demand
- Balances between specialization and flexibility

## 5. Storage System

### Model Definitions

Stores the complete model specifications:

- DAG structure with task relationships
- Task interfaces interfaces
  - Input and output tensor types

### Weight Files

Manages model weights for each task:

- Efficiently stored in safetensors format
- Accessible through standardized URI scheme

### Tensor Data

Handles intermediate and final computation results:

- Automatic garbage collection for unused tensors
- Efficient serialization and deserialization

## 6. Client Interface Components

### Model Deployment CLI

Enables model registration and partitioning:

- Analyzes model structure for optimal partitioning
- Creates task definitions with appropriate interfaces
- Uploads weight files to storage system
- Registers complete model with the system

### Node Management CLI

Facilitates node operation and monitoring:

- Registers node capabilities and specializations
- Manages stake deposits and withdrawals
- Monitors performance and earnings
- Controls specialization strategy

### User Interface

Provides task submission and monitoring:

- Submits computation requests with inputs
- Monitors execution progress
- Retrieves and visualizes results
- Manages payment and fee settings

## 7. Technical Specifications

### 7.1 Model DAG Structure

```
struct TensorSpec {
    string name;                // Tensor name
    string[] dimensions;        // Symbolic dimensions
    uint256[] shape;            // Concrete shape if known
    string dtype;               // Data type
}

struct TaskConnection {
    uint256 sourceTaskId;       // Source task (0 for model inputs)
    uint256 destinationTaskId;  // Destination task (0 for model outputs)
    uint256 sourceOutputIndex;  // Index in source task's outputs
    uint256 destInputIndex;     // Index in destination task's inputs
    TensorSpec tensorSpec;      // Specification of the tensor
}

struct ModelInfo {
    uint256 id;
    string name;
    string description;
    address owner;
    uint256[] taskIds;
    TaskConnection[] connections;
    bool isActive;
}
```

### 7.2 Task Definition

```
struct TaskInfo {
    uint256 id;
    uint256 modelId;
    string description;
    uint256 vramRequirement;
    uint256 computeUnits;       // Fixed computational complexity measure
    TensorSpec[] inputs;        // Input tensor specifications
    TensorSpec[] outputs;       // Output tensor specifications
    string weightUri;           // URI to weight file
}
```

Note: Each task represents a deterministic execution graph with a fixed number of GPU operations. The `computeUnits` field provides a standardized measure of computational complexity, enabling fixed and predictable pricing. This is possible because each task in the model, executed by TinyGrad, is also structured as a DAGs: the computations are sequential and not turing-complete, so they terminate after a fixed number of steps.

### 7.3 Node Specification

```
struct SupportedInterface {
    uint256 modelId;
    uint256 taskId;
}

struct NodeInfo {
    address owner;
    uint256 vramCapacity;
    uint256 stakeAmount;
    SupportedInterface[] supportedInterfaces;
    uint256 lastHeartbeat;
}
```

### 7.4 Execution Status

```
struct TaskExecutionStatus {
    uint256 taskId;
    address assignedNode;
    uint256 status;             // 0: pending, 1: ready, 2: in-progress, 3: completed, 4: failed
    uint256[] dependencyStatus; // Status of each dependency
    string[] inputUris;         // URIs to input tensors
    string[] outputUris;        // URIs to output tensors
    uint256 startTime;
    uint256 completionTime;
}

struct ModelExecutionStatus {
    uint256 id;
    uint256 modelId;
    address user;
    uint256 fee;
    TaskExecutionStatus[] taskStatuses;
    uint256 overallStatus;      // 0: pending, 1: in-progress, 2: completed, 3: failed
    string inputUri;            // Initial model input
    string outputUri;           // Final model output
    uint256 startTime;
    uint256 completionTime;
}
```

### 7.5 PoSP Security Parameters

- **Challenge Probability (p)**: 0.05-0.10 (5-10%)
- **Verification Reward (R)**: 1.2× computation cost
- **Slashing Amount (S)**: 10-20× computation cost
- **Maximum Collusion Fraction (r)**: 0.1 (10%)
- **Security Condition**: p > C/((1-r)(R+S))

## 8. Implementation Details

### 8.1 Performance Optimization

- **Deterministic Selection Algorithm**: Implement a fully deterministic selection algorithm that all nodes can independently compute and verify, enabling BFT consensus
- **Locality-Aware Assignment**: Implement geographical routing protocol to assign adjacent tasks to nodes in close network proximity
- **Parallel Execution Framework**: Create execution framework that automatically identifies and schedules independent DAG branches in parallel

### 8.2 Security Implementation

- **PoSP Protocol Parameters**: Set precise verification probability p=0.08 (8%) with fixed reward multiplier R=1.2x and slashing amount S=10x
- **Stake Requirements**: Require base stake of 1000 USDC plus 100 USDC per GB of VRAM claimed
- **Oracle Committee Protocol**: Implement 2-of-3 BFT consensus protocol for heartbeat monitoring with 2-minute detection window
- **VRF Implementation**: Use Solana's VRF service with entropy from a recent block hash for manipulation-resistant selection

### 8.3 Economic Implementation

- **Fee Structure**: Base fee = (computeUnits × 0.0001 USDC) + (min(priority × 0.05, 5) USDC) + (0.002 USDC per GB of VRAM)
- **Verification Compensation**: Validation tasks compensated at 100% of primary task compensation
- **Slashing Mechanism**: Dishonest behavior results in stake slashing of min(max(10 × taskFee, 500 USDC), totalStake)

### 8.4 Failure Handling

- **Node Timeout Protocol**: Declare node unresponsive after 3 consecutive missed heartbeats (1.5 minutes)
- **Task Timeout Implementation**: Task timeout = max(30s, 5s × computeUnits/100)
- **Reassignment Logic**: Automatically reassign task after timeout
- **Failure Tracking**: Implement exponential backoff for repeatedly failing tasks (2x timeout per failure)
- **Recovery Protocol**: Store execution checkpoint after each task completion to enable partial recovery
