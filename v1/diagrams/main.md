# System Flow Diagrams

I've checked through, I'm pretty sure these are (approximately) correct.

## Model Deployment

```mermaid
flowchart TD
    %% Client actors
    Client[Client]

    %% Model deployment tools
    subgraph "Model Deployment"
        DC[Deploy CLI]
        AP[Auto-Partitioner]
        TC[Graph Abstraction]
    end

    %% Blockchain contracts
    subgraph "Blockchain Layer"
        MR[Model Registry]
        TR[Task Registry]
    end

    %% Storage
    subgraph "Storage Layer"
        WS[Weight Storage]
    end

    %% MODEL DEPLOYMENT FLOW (RED)
    Client -->|"Deploy model"| DC
    DC -->|"1 - Parse Model"| TC
    TC -->|"2 - Create Partitions"| AP
    DC -->|"3 - Upload Weights"| WS
    AP -->|"4 - Infer Task Definitions"| DC
    DC -->|"5 - Register Tasks"| TR
    DC -->|"6 - Register Model, Referencing Tasks"| MR

    %% Style all relationships with red color
    linkStyle 0,1,2,3,4,5,6 stroke:#e74c3c,stroke-width:2;

    classDef redFlow fill:#e74c3c,stroke:#c0392b,color:white;
    class ModelDeployment redFlow;
```

## Node Setup

```mermaid
flowchart TD
    %% Node user
    NodeUser[Node User]

    %% Node components
    subgraph "SplitUp Node"
        NM[Node CLI]
        CF[Configuration Storage, State Service]
        subgraph "Compute Service"
            PR[Pre-loading Subsystem]
            IR[Iroh Networking]
            ES[Execution Subsystem]
        end
        TL[TaskListener Service]
        HS[Heartbeat Service]
    end

    %% Blockchain contracts
    subgraph "Blockchain Layer"
        NR[Node Registry]
        SC[Staking Contract]
    end

    %% Storage
    subgraph "Storage Layer"
        WS[Weight Storage]
    end

    %% NODE REGISTRATION FLOW (GREEN)
    NodeUser --> NM
    NM -->|"1 - Initial Setup"| CF
    CF -->|"2 - Configure Weight Management"| PR
    NM -->|"3 - Register Node"| NR
    NM -->|"4 - Submit Stake"| SC
    PR <-->|"5 - Cache Model Weights"| WS
    CF -->|"6 - Boot Up"| ES
    ES -->|"7 - Initialize Listener"| TL
    ES -->|"8 - Initialize Heartbeat"| HS

    %% Style all relationships with green color
    linkStyle 0,1,2,3,4,5,6,7,8 stroke:#2ecc71,stroke-width:2;

    classDef greenFlow fill:#2ecc71,stroke:#27ae60,color:white;
    class NodeRegistration greenFlow;
```

## Liveness Tracking System

Informs the Oracle Committee as to which nodes it should pick to perform the task.

```mermaid
flowchart TD
    %% Oracle Committee
    subgraph "Oracle Committee"
        OC[Oracle Consensus]
    end

    %% Node components
    subgraph "SplitUp Node"
        CS[Compute Service]
        HS[Heartbeat Service]
    end

    %% HEARTBEAT/LIVENESS FLOW (ORANGE)
    HS <-->|"1 - Report Capacity"| CS
    HS -->|"2 - Send Heartbeats"| OC
    OC -->|"3 - Track Liveness"| OC

    %% Style all relationships with orange color
    linkStyle 0,1,2 stroke:#e67e22,stroke-width:2;

    classDef orangeFlow fill:#e67e22,stroke:#d35400,color:white;
    class Heartbeat orangeFlow;
```

## Model Execution

```mermaid
flowchart TD
    %% Client actors at the top
    User[End User]
    UC[User CLI/UI]

    %% Storage
    subgraph "Storage Layer"
        TS[Tensor Storage]
    end

    %% Blockchain and Oracle layers
    subgraph "Blockchain Layer"
        ME[Model Execution]
        NR[Node Registry]
    end

    subgraph "Oracle Committee"
        OC[Oracle Consensus]
    end

    %% Node components
    subgraph "SplitUp Node"
        TL[TaskListener Service]
        CS[Compute Service]
        IN[Iroh Networking Module]
    end

    %% Downstream Node - positioned closer to where it's referenced
    subgraph "Downstream Node"
        DSN[Next Task Node]
    end

    %% TASK EXECUTION FLOW with logical flow direction
    User --> UC
    UC -->|"1 - Upload Input Tensors"| TS
    UC -->|"2 - Request Execution"| ME
    ME -->|"3 - Request Execution Plan"| OC
    OC <-->|"4 - Get Specialized Nodes"| NR
    OC -->|"5 - Generate Access Control"| TS
    OC -->|"6 - Submit Node Assignment Plan"| ME
    ME -->|"7 - Notify Nodes"| TL
    TL -->|"8 - Forward Task To GPU"| CS
    CS -->|"9 - Compute Task"| CS
    CS -->|"10 - Store Result"| TS

    %% Direct Node Communication (organized to minimize crossing)
    CS -->|"11a - Direct Notification"| IN
    IN -->|"12a - Notify Next Node"| DSN
    CS -->|"11b - Report Completion"| ME

    %% Style task execution relationships with blue color
    linkStyle 0,1,2,3,4,5,6,7,8,9,10,11,12,13 stroke:#3498db,stroke-width:2;

    classDef blueFlow fill:#3498db,stroke:#2980b9,color:white;
    class TaskExecution blueFlow;
```

## Compute Verification Flows

```mermaid
flowchart TD
    %% Blockchain contracts
    subgraph "Blockchain Layer"
        ME[Model Execution]
        VC[Verification Contract]
        SC[Staking Contract]
        VRF[Verifiable Random Function]
        NR[Node Registry]
    end

    %% Oracle Committee
    subgraph "Oracle Committee"
        OC[Oracle Consensus]
    end

    %% Node components
    subgraph "SplitUp Node"
        CS[Compute Service]
        TL[TaskListener Service]
    end

    %% Storage
    subgraph "Storage Layer"
        TS[Tensor Storage]
    end

    %% VERIFICATION FLOW (PURPLE)
    %% Main verification path
    ME -->|"1 - Request Verification"| VC
    VC -->|"2 - Check Verification Threshold"| VRF

    %% Normal path (92% probability)
    VRF -->|"3a - Skip Re-computation (92%)"| VC
    VC -->|"4a - Apply Standard Rewards"| SC

    %% Re-computation path (8% probability)
    VRF -.->|"3b - Trigger Re-computation (8%)"| VC
    VC -.->|"4b - Select Verifiers"| OC
    OC -.->|"5b - Assign to Different Node"| ME
    ME -.->|"6b - Select Different Node"| NR
    NR -.->|"7b - Node Listens For Verification Task"| TL
    TL -.->|"8b - Forward Verification Task"| CS
    CS -.->|"10b - Store Verification Result"| TS
    TS -.->|"11b - Compare Results"| VC
    VC -.->|"12b - Apply Penalties/Rewards Based on Comparison"| SC

    %% Style all normal relationships with purple color
    linkStyle 0,1,2,3 stroke:#9b59b6,stroke-width:2;

    %% Style all probabilistic relationships with dashed purple
    linkStyle 4,5,6,7,8,9,10,11,12 stroke:#9b59b6,stroke-width:2,stroke-dasharray: 5 5;

    classDef purpleFlow fill:#9b59b6,stroke:#8e44ad,color:white;
    classDef purpleDashedFlow fill:#9b59b6,stroke:#8e44ad,color:white,stroke-dasharray: 5 5;
    class NormalV purpleFlow;
    class ProbV purpleDashedFlow;
```
