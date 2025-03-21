# SplitUp: A First-Principles Explanation (Complete)

## 1. The Core Problem

Modern AI models like LLaMA-70B require 80-140GB of VRAM (Video RAM on graphics cards), but consumer GPUs typically only have 8-24GB. This creates a fundamental limitation: even if you have a powerful consumer GPU, you simply can't run these large models on your hardware.

## 2. Our Solution: High-Level Overview

SplitUp allows large AI models to run across multiple consumer GPUs by:

1. Breaking models into smaller "tasks" that function as pure computations with typed inputs and outputs
2. Creating a marketplace where GPU owners can specialize in specific tasks
3. Coordinating the execution of these tasks to run complete models
4. Ensuring correct results through efficient verification (only 8% overhead)
5. Using USDC for payments and economic security guarantees

## 3. The Technical Components

### 3.1. Model Partitioning

**Problem:** Large models don't fit in consumer GPU memory

**Solution:** We automatically split models into smaller pieces (tasks)

```
ModelDev->>CLI: "splitup-deploy register --model llama-70b.pkl --target-vram 12GB"
```

This process:

- Loads the model using TinyGrad (a lightweight ML framework)
- Analyzes its computational graph (the mathematical flow of operations)
- Finds optimal split points where memory usage peaks
- Creates independent tasks with strictly typed tensor interfaces between them

**Key Terms:**

- **Computational graph**: A representation of all mathematical operations in the model as a flowchart
- **Task**: A pure function that takes typed tensor inputs and produces typed tensor outputs
- **Tensor**: A multi-dimensional array with explicit shape and data type (e.g., int8, float16, float32)

### 3.2. Task & Model Structure Definition

After partitioning, we explicitly define:

1. Each individual task with its typed tensor interfaces
2. How the tasks connect to form the complete model

We use Solana smart contracts for this:

```
CLI->>TaskRegistry: registerTask(modelId, description, vramRequirement, inputTensors, outputTensors, weightUri)
CLI->>ModelRegistry: registerModel(name, description, taskIds, connections)
```

**Key Terms:**

- **Task Registry**: Contract that stores task definitions with explicit input and output tensor specifications
- **Model Registry**: Contract that stores how tasks connect to form a model
- **DAG (Directed Acyclic Graph)**: A flowchart structure showing which tasks depend on others
- **Weight URI**: A reference to where the model weights are stored (not on Solana)

The Model Registry verifies that tasks connect properly, with exact matching input/output tensor shapes, types, and dimensions with no circular dependencies.

### 3.3. Decentralized Storage Strategy

Because Solana can't efficiently store large files, we use external decentralized storage for:

1. Model weights (parameters that define the model's behavior)
2. Input tensors
3. Intermediate tensor results between tasks
4. Final output tensors

**Key Storage Implementation Details:**

- Each tensor has a unique URI
- Tensors include explicit type information (TensorSpec) including dimensions, shape, and data type
- Intermediate tensors have automatic time-to-live for garbage collection
- We're implementing a specialized storage backend for efficient tensor operations
- Nodes handling adjacent tasks can maintain local copies to reduce transfer costs

This separation means Solana only handles coordination, while actual tensor data flows through external storage.

### 3.4. Node Specialization

Instead of requiring every node to run every task, nodes specialize in specific pure function tasks:

```
NodeOp->>NodeCLI: "splitup-node register --vram-capacity 24GB --model-id llama-70b --tasks 1,2"
```

When registering, a node:

1. Declares its exact VRAM capacity
2. Selects specific tasks to specialize in
3. Pre-loads weights for those tasks into GPU memory
4. Stakes USDC as security collateral

**Key Terms:**

- **Pre-loading**: Loading model weights into GPU memory in advance for instant execution
- **Staking**: Depositing USDC as security against dishonest behavior
- **Specialization**: Focusing on specific tasks rather than the whole model
- **Task Execution**: Processing input tensors through deterministic operations to produce output tensors

### 3.5. Node Liveness System

To ensure system reliability, we implement a comprehensive liveness tracking system:

1. **Heartbeat Mechanism**:

   - Each node sends heartbeats every 30 seconds
   - Heartbeats include node status and VRAM availability
   - Missing heartbeats trigger a grace period before a node is marked offline

2. **Failure Detection**:
   - After 3 consecutive missed heartbeats (90 seconds), a node is marked offline
   - Active tasks receive timeout warnings
   - Tasks are reassigned after their specific timeout period expires

### 3.6. Execution Coordination

When a user wants to run an inference:

```
Client->>ModelContract: executeModel(modelId, inputUri, maxFee)
```

The Model Execution contract then:

1. Retrieves the model's DAG structure with explicit tensor flow definitions
2. Identifies which tasks are ready to execute (all input tensors available)
3. Selects specialized nodes for each task
4. Tracks completion and tensor data flow between tasks

**Node Selection Process:**

1. **Filtering**: Find all live nodes specialized in the required task
2. **Deterministic Selection**: Use a verifiable random function (VRF) seeded with a block hash

**Task Timeout Handling:**

- Each task has a dynamic timeout based on its computational complexity (computeUnits)
- If a task fails, it's reassigned with exponential backoff (double timeout)
- After 3 failures, a task is flagged for special handling
- The system maintains checkpoints after each task completion for partial recovery

### 3.7. Oracle Committee

The Oracle Committee provides critical oversight functions:

1. **Committee Structure**:

   - (Probably) 3 nodes with large stakes
   - Periodically rotated to prevent centralization
   - Requires 2/3 majority for consensus decisions

2. **Core Responsibilities**:

   - Monitoring node liveness through heartbeat consensus
   - Validating that the node selection algorithm executed correctly
   - Resolving verification disputes by comparing tensor outputs
   - Providing inputs for the verifiable random function

3. **Dispute Resolution**:
   - When verification results conflict, the committee retrieves and compares both tensor outputs
   - Identifies honest and dishonest parties
   - Authorizes appropriate slashing penalties or rewards

The Oracle Committee ensures Byzantine Fault Tolerance and provides essential trust minimization.

### 3.8. Verification: Proof of Sampling Protocol (PoSP)

Traditional verification would double costs by running every task twice. Our PoSP approach is much more efficient:

1. For each task, there's only an 8% probability of verification
2. If selected, a second node re-computes the pure function task with identical inputs
3. Output tensors are compared for exact equality
4. Economic incentives make honesty more profitable than cheating

**Verification Process:**

- The Verification Contract uses VRF to determine if verification is needed
- If triggered, the Oracle Committee selects a validator (different from the original node)
- The validator executes the same task independently with identical input tensors
- Results are compared by tensor hash, with disputes resolved by the Oracle Committee

**Economics of Verification:**

- If a node is honest: It receives payment in USDC
- If a node cheats and isn't caught (92% chance): It receives payment without doing the work
- If a node cheats and is caught (8% chance): It loses staked USDC worth 10x the task payment

### 3.10. Economic Security Model

The system uses a precisely calibrated economic model:

- Nodes stake USDC as security collateral (1000 USDC base + 100 USDC per GB of VRAM)
- Task payments are fixed based on computational complexity (computeUnits)
- Verification rewards are 1.2x the computation cost
- Slashing penalties are 10x the computation cost

The mathematical security condition is:

```
p > C/((1-r)(R+S))
```

Where:

- p = verification probability (8%)
- C = computation cost
- r = maximum collusion fraction (10%)
- R = verification reward (1.2x)
- S = slashing amount (10x)

With these parameters, dishonesty has negative expected value, ensuring system integrity.

## 4. The Complete Workflow

Let's walk through the entire process:

### 4.1. Preparation Phase

1. **Model Registration**:

   - Developer partitions model into pure function tasks with typed tensor interfaces
   - Uploads weights to decentralized storage
   - Registers tasks and model structure on Solana with explicit tensor specifications

2. **Node Registration**:
   - GPU owners register their hardware with exact VRAM capacity
   - Stake USDC as security
   - Specialize in specific tasks by pre-loading weights
   - Begin sending regular heartbeats to prove availability

### 4.2. Execution Phase

1. **Inference Request**:

   - User uploads input tensors
   - Submits request with maximum fee in USDC
   - Model Execution contract begins orchestration

2. **Task Assignment**:

   - Contract identifies ready tasks (all input tensors available)
   - Selects specialized nodes for each task
   - Nodes retrieve input tensors from storage

3. **Computation**:

   - Nodes execute pure function tasks
   - Upload output tensors to storage
   - Report completion with output tensor URIs

4. **Verification**:

   - 8% of tasks randomly verified by other nodes
   - Output tensors compared for exact equality
   - Disputes resolved by Oracle Committee
   - USDC payments and penalties distributed

5. **Result Delivery**:
   - Final output tensor URI returned to user
   - User retrieves complete result from storage

## 5. Advanced Features

1. **Fault Tolerance**: If a node fails (detected by missing heartbeats), the task is automatically reassigned with appropriate backoff.

2. **Multi-Task Assignment**: Nodes with higher VRAM can handle multiple adjacent tasks, improving efficiency by reducing tensor transfer overhead.

3. **Parallel Execution**: Independent branches of the model execute simultaneously on different nodes, following the DAG structure.

4. **Checkpoint Recovery**: The system maintains execution state checkpoints after each task, enabling partial recovery by preserving all intermediate tensors.

5. **Dynamic Task Prioritization**: Critical path tasks receive higher priority to minimize overall latency.

By constructing this system from first principles, SplitUp creates a decentralized marketplace that makes large AI models accessible on consumer hardware with mathematical security guarantees and robust operational reliability.
