# SplitUp Oracle Committee: Consensus Protocol Specification

This document details the Oracle Committee consensus protocol in the SplitUp network, focusing on how liveness data is tracked, consensus is reached, and computation nodes are selected.

## System Overview

The SplitUp Oracle Committee is a Byzantine Fault Tolerant (BFT) system consisting of multiple oracle nodes that work together to:

1. Track the liveness status of all compute nodes in the network
2. Reach consensus about which nodes are currently online and available
3. Provide deterministic node selection recommendations to the blockchain
4. Validate node selection algorithms for fairness and correctness
5. Ensure economic security through multi-signature authorizations

```mermaid
graph TD
    subgraph "Blockchain Layer"
        ME[Model Execution]
    end

    subgraph "Oracle Committee (BFT)"
        O1[Oracle Node 1]
        O2[Oracle Node 2]
        O3[Oracle Node 3]

        O1 <--> O2
        O2 <--> O3
        O3 <--> O1
    end

    subgraph "Compute Nodes"
        CN1[Compute Node 1]
        CN2[Compute Node 2]
        CN3[Compute Node 3]
        CNn[Compute Node n]
    end

    CN1 --> O1
    CN1 --> O2
    CN1 --> O3

    CN2 --> O1
    CN2 --> O2
    CN2 --> O3

    CN3 --> O1
    CN3 --> O2
    CN3 --> O3

    CNn -.-> O1
    CNn -.-> O2
    CNn -.-> O3

    O1 --> ME
    O2 --> ME
    O3 --> ME
```

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

## Network Communication Protocols

### Oracle-to-Oracle Protocol

```mermaid
sequenceDiagram
    participant O1 as Oracle Node 1
    participant O2 as Oracle Node 2
    participant O3 as Oracle Node 3

    Note over O1,O3: Liveness Table Synchronization (30s)

    O1->>O1: Update local liveness table
    O2->>O2: Update local liveness table
    O3->>O3: Update local liveness table

    O1->>O2: ProposeUpdate(LivenessUpdate)
    O1->>O3: ProposeUpdate(LivenessUpdate)

    O2->>O1: ProposeUpdate(LivenessUpdate)
    O2->>O3: ProposeUpdate(LivenessUpdate)

    O3->>O1: ProposeUpdate(LivenessUpdate)
    O3->>O2: ProposeUpdate(LivenessUpdate)

    Note over O1,O3: BFT Consensus Round

    O1->>O2: VoteLivenessTable(hash, signature)
    O1->>O3: VoteLivenessTable(hash, signature)

    O2->>O1: VoteLivenessTable(hash, signature)
    O2->>O3: VoteLivenessTable(hash, signature)

    O3->>O1: VoteLivenessTable(hash, signature)
    O3->>O2: VoteLivenessTable(hash, signature)

    Note over O1,O3: Finalize Consensus

    O1->>O1: Validate 2/3 majority
    O2->>O2: Validate 2/3 majority
    O3->>O3: Validate 2/3 majority
```

### Oracle-to-Blockchain Protocol

```mermaid
sequenceDiagram
    participant BC as Blockchain
    participant O1 as Oracle Node 1
    participant O2 as Oracle Node 2
    participant O3 as Oracle Node 3

    BC->>O1: RequestNodeSelection(taskId, modelId, vrf_seed)
    BC->>O2: RequestNodeSelection(taskId, modelId, vrf_seed)
    BC->>O3: RequestNodeSelection(taskId, modelId, vrf_seed)

    Note over O1,O3: Run deterministic selection algorithm

    O1->>O1: SelectNodes(LivenessTable, vrf_seed)
    O2->>O2: SelectNodes(LivenessTable, vrf_seed)
    O3->>O3: SelectNodes(LivenessTable, vrf_seed)

    O1->>O1: Sign selection
    O2->>O2: Sign selection
    O3->>O3: Sign selection

    O1->>O1: Store OracleSignedNodeSelection
    O2->>O1: POST OracleSignedNodeSelection
    O3->>O1: POST OracleSignedNodeSelection

    O1->>O1: Aggregate OracleSignedNodeSelection into CommitteeSignedNodeSelection

    O1->>BC: Commit CommitteeSignedNodeSelection

    BC->>BC: Verify 2/3 matching signatures
    BC->>BC: Process node selection
```

## Data Types Specification

### Oracle Committee Types

```typescript
/** Oracle node identifier */
export type OracleId = string;

/** Consensus round identifier */
export type RoundId = number;

/** Hash of liveness table */
export type TableHash = string;

/** Liveness update for a specific node */
export interface LivenessUpdate {
  nodeAddress: NodeAddress; // Address of the node
  lastHeartbeat: Timestamp; // Last heartbeat time
  status: NodeStatus; // Current status
  hasCapacity: boolean; // Whether node has capacity
  oracleId: OracleId; // Oracle that received the update
  updateTime: Timestamp; // When update was received
}

/** Complete node liveness table */
export interface LivenessTable {
  roundId: RoundId; // Current consensus round
  updates: LivenessUpdate[]; // All node updates
  tableHash: TableHash; // Hash of the sorted table
  timestamp: Timestamp; // When table was created
}

/** Vote on a liveness table */
export interface LivenessVote {
  oracleId: OracleId; // Voting oracle
  roundId: RoundId; // Round being voted on
  tableHash: TableHash; // Hash being voted for
  signature: string; // Signature of the vote
  timestamp: Timestamp; // When vote was cast
}

/** Node selection for a task */
export interface NodeSelection {
  taskId: string; // Task to be executed
  selectedNodes: NodeAddress[]; // Selected nodes in priority order
  vrfSeed: string; // Seed used for selection
  roundId: RoundId; // Liveness round used
  timestamp: Timestamp; // When selection was made
}

/** Signed node selection from individual oracle **/
export interface OracleSignedNodeSelection: {
  selection: NodeSelection;
  signature: string;
}

/** Signed node selection */
export interface CommitteeSignedNodeSelection {
  selection: NodeSelection; // The node selection
  signatures: {
    // Signatures from oracles
    [oracleId: string]: string;
  };
}
```

## Protocol Flows with Explicit Type References

### Heartbeat Collection Flow

```mermaid
sequenceDiagram
    participant CN as Compute Node
    participant O1 as Oracle Node 1
    participant O2 as Oracle Node 2
    participant O3 as Oracle Node 3

    Note over CN,O3: Heartbeat Distribution

    CN->>CN: Generate HeartbeatData{timestamp, nodeStatus, hasCapacity}
    CN->>CN: Sign to create SignedHeartbeatData

    par Send to all Oracle nodes
        CN->>O1: POST /api/heartbeat (SignedHeartbeatData)
        CN->>O2: POST /api/heartbeat (SignedHeartbeatData)
        CN->>O3: POST /api/heartbeat (SignedHeartbeatData)
    end

    par Process heartbeats
        O1->>O1: Create LivenessUpdate from heartbeat
        O2->>O2: Create LivenessUpdate from heartbeat
        O3->>O3: Create LivenessUpdate from heartbeat
    end

    O1->>O1: Update local LivenessTable
    O2->>O2: Update local LivenessTable
    O3->>O3: Update local LivenessTable
```

### Consensus Protocol Flow

```mermaid
sequenceDiagram
    participant O1 as Oracle Node 1
    participant O2 as Oracle Node 2
    participant O3 as Oracle Node 3

    Note over O1,O3: Consensus Round Start

    O1->>O1: Generate LivenessTable{roundId, updates, tableHash}
    O2->>O2: Generate LivenessTable{roundId, updates, tableHash}
    O3->>O3: Generate LivenessTable{roundId, updates, tableHash}

    Note over O1,O3: Table Exchange Phase

    par Exchange liveness tables
        O1->>O2: POST /api/liveness/propose (LivenessTable)
        O1->>O3: POST /api/liveness/propose (LivenessTable)

        O2->>O1: POST /api/liveness/propose (LivenessTable)
        O2->>O3: POST /api/liveness/propose (LivenessTable)

        O3->>O1: POST /api/liveness/propose (LivenessTable)
        O3->>O2: POST /api/liveness/propose (LivenessTable)
    end

    Note over O1,O3: Vote Phase

    O1->>O1: Merge received tables
    O2->>O2: Merge received tables
    O3->>O3: Merge received tables

    O1->>O1: Generate LivenessVote{roundId, tableHash, signature}
    O2->>O2: Generate LivenessVote{roundId, tableHash, signature}
    O3->>O3: Generate LivenessVote{roundId, tableHash, signature}

    par Exchange votes
        O1->>O2: POST /api/liveness/vote (LivenessVote)
        O1->>O3: POST /api/liveness/vote (LivenessVote)

        O2->>O1: POST /api/liveness/vote (LivenessVote)
        O2->>O3: POST /api/liveness/vote (LivenessVote)

        O3->>O1: POST /api/liveness/vote (LivenessVote)
        O3->>O2: POST /api/liveness/vote (LivenessVote)
    end

    Note over O1,O3: Finalization Phase

    O1->>O1: Tally votes, check for 2/3 majority
    O2->>O2: Tally votes, check for 2/3 majority
    O3->>O3: Tally votes, check for 2/3 majority

    O1->>O1: Finalize consensus LivenessTable
    O2->>O2: Finalize consensus LivenessTable
    O3->>O3: Finalize consensus LivenessTable
```

### Node Selection Flow

```mermaid
sequenceDiagram
    participant MC as Model Contract
    participant O1 as Oracle Node 1
    participant O2 as Oracle Node 2
    participant O3 as Oracle Node 3

    MC->>O1: RequestNodeSelection(taskId, modelId, vrf_seed)
    MC->>O2: RequestNodeSelection(taskId, modelId, vrf_seed)
    MC->>O3: RequestNodeSelection(taskId, modelId, vrf_seed)

    par Run selection algorithm
        O1->>O1: Apply deterministic selection
        O2->>O2: Apply deterministic selection
        O3->>O3: Apply deterministic selection
    end

    par Generate and sign selection
        O1->>O1: Create NodeSelection
        O2->>O2: Create NodeSelection
        O3->>O3: Create NodeSelection

        O1->>O1: Sign NodeSelection
        O2->>O2: Sign NodeSelection
        O3->>O3: Sign NodeSelection
    end

    O1->>O1: Store OracleSignedNodeSelection
    O2->>O1: POST OracleSignedNodeSelection
    O3->>O1: POST OracleSignedNodeSelection

    O1->>O1: Aggregate OracleSignedNodeSelection into CommitteeSignedNodeSelection

    O1->>MC: Commit CommitteeSignedNodeSelection

    MC->>MC: Verify 2/3 matching selections and signatures
    MC->>MC: Proceed with task assignment
```

## Implementation Details

### 1. BFT Consensus Protocol

**Consensus Process**:

- Consensus runs in rounds (every 30 seconds)
- Each oracle independently tracks heartbeats from compute nodes
- Oracles exchange their view of the network
- 2/3 majority required to reach consensus
- Consensus result becomes the authoritative liveness table

**Offline Node Detection**:

- Nodes missing 3 consecutive heartbeats are marked offline
- Oracle Committee requires 2/3 agreement to change node status
- Status transitions have hysteresis to prevent flapping

### 2. Deterministic Node Selection

**Selection Algorithm**:

- Inputs: task requirements, consensus liveness table, VRF seed
- Filter: Match only online nodes with capacity and required specialization
- Ranking: Apply deterministic function based on VRF seed, stake amount, and performance history
- Multi-select: Choose primary and backup nodes if needed

**Selection Security**:

- VRF seed comes from recent blockchain state
- Selection algorithm is pure and deterministic
- All oracles must produce identical results
- Multi-signature prevents manipulation by minority of oracles

### 3. Oracle Committee Structure

**Committee Membership**:

- Initially 3 oracle nodes (2/3 majority threshold)
- (TODO) Economic slashing for malicious behavior

**Oracle Redundancy**:

- System remains functional if minority of oracles fail
- Each compute node sends heartbeats to all oracles
- Oracle Committee members are geographically distributed

## API Specifications

### 1. Heartbeat Collection API

**Endpoint**: `POST /api/heartbeat`

**Request Body**: `SignedHeartbeatData`

- Identical to standard heartbeat protocol
- Must include valid signature

**Response**: `HeartbeatResponse`

- Indicates acceptance

**Processing**:

- Oracle verifies signature
- Oracle stores heartbeat in local database
- Oracle prepares for next consensus round

### 2. Consensus Protocol API

**Endpoint**: `POST /api/liveness/propose`

**Request Body**: `LivenessTable`

- Current view of network liveness from an oracle

**Response**: Simple acknowledgment

**Endpoint**: `POST /api/liveness/vote`

**Request Body**: `LivenessVote`

- Vote on a specific table hash

**Response**: Simple acknowledgment

### 3. Node Selection API

**Endpoint**: `POST /api/selection/request`

**Request Body**:

```typescript
{
  taskId: string;
  modelId: string;
  vrfSeed: string;
  requirements: {
    minVram: number;
    specializations: string[];
  }
}
```

**Response**: `CommitteeSignedNodeSelection`

- Contains selection with oracle signatures

## Conclusion

The SplitUp Oracle Committee provides a crucial BFT consensus layer that ensures reliable tracking of node liveness without requiring on-chain storage of this rapidly changing state. By reaching agreement on which nodes are available, the committee enables deterministic node selection for task execution while maintaining the security and fault tolerance guarantees required by the network.

This approach combines:

1. **Efficiency**: Keeping rapidly changing liveness data off-chain
2. **Security**: Using BFT consensus to prevent manipulation
3. **Determinism**: Ensuring consistent node selection
4. **Redundancy**: Operating through oracle failures
5. **Economic Security**: Aligning incentives through staking

Together, these properties allow the SplitUp network to efficiently distribute computation across nodes while maintaining security guarantees.
