# SplitUp: Large AI Model Marketplace on Solana

> **TLDR: A Solana-powered marketplace where consumer GPU owners earn by running specialized portions of large AI models that wouldn't otherwise fit on their hardware.**

---

## The Problem: Large Models Don't Fit on Consumer Hardware

- **Hard Technical Limit**: Modern AI models require 24-80GB VRAM
- **Consumer Reality**: Most GPUs have only 8-16GB VRAM
- **Current Options**:
  - Buy expensive specialized hardware ($5,000-10,000+)
  - Pay for cloud GPU instances ($2-8+ per hour)
  - Use smaller, less capable models

This creates a significant barrier to AI democratization.

---

## Introducing SplitUp: AI Compute Marketplace

**SplitUp creates a two-sided marketplace on Solana:**

- **Buyers**: AI developers who need to run large models
- **Sellers**: GPU owners who specialize in specific model components

The correctness of computations is ensured through our Proof of Sampling Protocol (PoSP) with only 8% verification overhead - dramatically more efficient than traditional verification methods that require 100%+ redundancy.

Result: Consumer GPUs can collectively run models too large for any single one... and it's cheap.

---

## Why SplitUp is Special: Technical Advantages

**Built on EigenTensor's breakthrough technology:**

1. **Memory Safety**: No arbitrary code execution - only memory-safe tensor operations allowed

   - Prevents security exploits or physical hardware damage
   - Enables trustless computation with mathematical guarantees

2. **GPU Agnosticism**: Works on any consumer GPU regardless of manufacturer

   - NVIDIA, AMD, Intel all supported
   - Nodes compile optimized code for their specific hardware

3. **Tensor-Centric Computation**: Universal format for any ML workload

   - Compatible with popular frameworks (PyTorch, TensorFlow models)
   - Entire models represented as computational graphs
   - TinyGrad compatible - familiar API for ML developers

4. **Automatic Model Splitting**: VRAM no longer limits model size

   - Novel partitioning algorithm finds optimal split points
   - Memory requirements distributed across multiple nodes
   - Solves the #1 bottleneck in AI democratization

5. **Efficient Verification**: Only 8% of work needs verification
   - Proof of Sampling Protocol vs traditional 100%+ overhead
   - Economic incentives make honesty more profitable than cheating

No other platform combines all these advantages in a working marketplace.

---

## How It Works: The Big Picture

```mermaid
flowchart LR
    subgraph "1. Split Large Model"
        LM[Large 70B Model] --> |Partition| P1[Task 1: 12GB] & P2[Task 2: 12GB] & P3[Task 3: 12GB] & P4["..."] & P5[Task 12: 12GB]
    end

    subgraph "2. Distribute to Specialized Nodes"
        P1 --> |Assign| N1[Node A]
        P2 --> |Assign| N2[Node B]
        P3 --> |Assign| N3[Node C]
        P4 --> |Assign| N4["..."]
        P5 --> |Assign| N5[Node L]
    end

    subgraph "3. Execute & Verify 8%"
        N1 --> R1[Result 1]
        N2 --> R2[Result 2]
        N3 --> R3[Result 3]
        N4 --> R4["..."]
        N5 --> R5[Result 12]
    end

    subgraph "4. Combine Results"
        R1 & R2 & R3 & R4 & R5 --> FR[Final Result]
    end

    style LM fill:#ff9999
    style FR fill:#99ff99
    style N1 fill:#9999ff
    style N2 fill:#9999ff
    style N3 fill:#9999ff
    style N4 fill:#9999ff
    style N5 fill:#9999ff
```

---

## Technical Deep Dive: EigenTensor Integration

```python
# Define your model using TinyGrad-compatible code
def create_llama_task(context: TensorContext) -> GraphProgram:
    # Define placeholder tensors for token embeddings
    input_ids = context.add_graph_input("input_ids", (1, max_seq_len))

    # Load model architecture (weights handled separately)
    model = LLaMAModel(config)

    # Define forward pass (automatically builds computational graph)
    outputs = model(input_ids)

    # Compile to universal tensor graph format
    return context.compile_to_graph(outputs)

# Auto-partition the model for distributed execution
def auto_partition(
    graph_program: GraphProgram,
    target_vram: int
) -> list[SolanaTaskDefinition]:
    # Analyze model memory requirements and dependencies
    partitions = split_graph_by_memory_constraints(graph_program, target_vram)

    # Define clean interfaces between partitions
    task_definitions = []
    for partition in partitions:
        task_definition = SolanaTaskDefinition(
            task_id=generate_task_id(),
            vram_requirement=calculate_vram_needs(partition),
            weight_uri=upload_weights_to_storage(partition),
            input_interfaces=define_input_interfaces(partition),
            output_interfaces=define_output_interfaces(partition)
        )
        task_definitions.append(task_definition)

    return task_definitions
```

SplitUp transforms this memory-safe computation into a Solana marketplace.

---

## Solana-powered Marketplace

```mermaid
sequenceDiagram
    participant Client as AI Developer
    participant Contract as Solana Smart Contracts
    participant Node as GPU Node Operators

    Client->>Contract: 1. Post Job (model, input, maxFee)
    Contract->>Contract: 2. Calculate optimal task division
    Contract->>Node: 3. Offer tasks to specialized nodes
    Node->>Contract: 4. Accept tasks (stake as collateral)
    Node->>Node: 5. Execute specialized tasks
    Node->>Contract: 6. Submit results
    Contract->>Contract: 7. Verify 8% of results randomly
    Contract->>Node: 8. Pay for honest execution
    Contract->>Client: 9. Return complete results
```

The marketplace uses SOL for payments and staking with bonded economic guarantees.

---

## Market Dynamics & Incentives

**For GPU Owners (Sellers):**

- **Earnings**: ~$0.10-0.50 per hour per GPU depending on task specialization
- **Specialization**: Choose specific model components to specialize in
- **Requirements**: Stake SOL as security deposit (slashed if dishonest)
- **Optimization**: Run multiple adjacent tasks for higher earnings

**For AI Developers (Buyers):**

- **Access**: Run 70B+ models without specialized hardware
- **Cost**: Pay only for compute used (~$0.25-1.00 per inference)
- **Interface**: Simple API similar to centralized alternatives
- **Control**: Own your data and model weights

---

## Comparison: What Makes Us Unique

| Feature                   | SplitUp                       | Other Decentralized    |
| ------------------------- | ----------------------------- | ---------------------- |
| **Large Model Support**   | ✓ Any size via partitioning   | ✗ Limited by node VRAM |
| **Memory Safety**         | ✓ Only tensor operations      | ✓ Limited operations   |
| **GPU Agnosticism**       | ✓ Any GPU hardware            | ✗ Often specific GPUs  |
| **Model Splitting**       | ✓ Automatic partitioning      | ✗ Not supported        |
| **Verification Overhead** | ✓ Just 8% (PoSP)              | ~ Larger overheads     |
| **Marketplace Model**     | ✓ Open on Solana              | ✓ Limited efficiency   |
| **Flexibility**           | ✓ Any tensor DAG via TinyGrad | ✗ Limited model types  |
| **Developer Experience**  | ✓ TinyGrad compatible         | ✗ Complex custom APIs  |

---

## Concrete Example: Running LLaMA-70B on SplitUp

**Traditional Approach:**

- Requires A100 GPU (~$10,000) or cloud instance ($2-8/hour)
- VRAM limitation forces expensive hardware choices

**SplitUp Approach:**

- Model automatically partitioned into 12 tasks of ~12GB each
- Memory-safe task definitions registered on Solana
- Tasks distributed to specialized nodes (RTX 3060+ GPUs)
- Results combined into complete inference output
- Total cost: ~$0.50 per inference vs. $2+ on cloud platforms

This makes state-of-the-art models accessible to everyone.

---

## Technical Architecture

```mermaid
flowchart TD
    subgraph Solana
        MR[Model Registry]
        TR[Task Registry]
        NR[Node Registry]
        ME[Model Execution]
        VR[Verification]
        SM[Staking Management]
    end

    subgraph "EigenTensor Layer"
        GC[Graph Compiler]
        SP[Splitting Engine]
        MS[Memory Safety]
    end

    subgraph "Node Software"
        TE[Task Executor]
        PS[Pre-loading System]
        HS[Heartbeat Service]
    end

    subgraph "Client Interfaces"
        DC[Developer Console]
        MC[Model Conversion]
        NM[Node Management]
    end

    subgraph "Storage"
        WS[Weight Storage]
        TS[Tensor Storage]
    end

    Client[AI Developer] --> DC
    NodeOp[GPU Owner] --> NM
    DC --> GC
    GC --> SP
    DC --> ME
    ME --> NR
    ME --> MR
    ME --> TR
    ME --> VR
    VR --> SM
    NM --> NR
    NM --> SM
    NR --> TE
    TE <--> TS
    TE <--> WS
    PS <--> WS
    HS --> NR
    SP --> MR
    SP --> TR
    MS --> TE
```

---

## Hackathon Implementation

We've built a functional prototype demonstrating:

- **EigenTensor integration** with memory-safe tensor operations
- **Partitioning engine** that divides models into VRAM-constrained tasks
- **Solana contracts** for marketplace coordination
- **Proof of Sampling** implementation (8% verification)
- **Economic model** for staking and payments

Demo: Partitioning LLaMA-70B for execution across consumer GPUs

---

## Join Our Marketplace

**For AI Developers**:

- Access large models without expensive hardware
- Pay only for what you use, no upfront costs
- Simple API for model execution

**For GPU Owners**:

- Earn SOL by joining our compute marketplace
- Specialize in high-demand model components
- Low barrier to entry with consumer hardware

GitHub: github.com/splitup/splitup

---

## Thank You

**SplitUp: The Solana-powered Marketplace for Distributed AI Computation**

Contact: team@splitup.dev

[Created for the 2023 Solana Hackathon]
