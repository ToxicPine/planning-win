use anchor_lang::prelude::*;

pub type TensorUri = String; // URI pointing to tensor data
pub type WeightUri = String; // URI pointing to weight data

#[derive(AnchorSerialize, AnchorDeserialize, Clone, PartialEq)]
pub enum TaskExecutionState {
    Pending,
    Assigned,
    InProgress,
    Completed,
    Failed,
    PendingVerification,
    Verified,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct TensorSpec {
    pub name: String,            // Tensor name
    pub dimensions: Vec<String>, // Symbolic dimensions
    pub shape: Option<Vec<u64>>, // Concrete shape if known
    pub dtype: String,           // Data type
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct TaskConnection {
    pub source_task_id: u64,      // Source task (0 for model inputs)
    pub destination_task_id: u64, // Destination task (0 for model outputs)
    pub source_output_index: u64, // Index in source task's outputs
    pub dest_input_index: u64,    // Index in destination task's inputs
    pub tensor_spec: TensorSpec,  // Specification of the tensor
}

#[account]
pub struct OracleCommittee {
    pub members: Vec<Pubkey>,
}

#[account]
pub struct TaskInfo {
    pub id: u64,
    pub model_id: u64,
    pub description: String,
    pub vram_requirement: u64,
    pub compute_units: u64,       // Fixed computational complexity
    pub inputs: Vec<TensorSpec>,  // Input tensor specs
    pub outputs: Vec<TensorSpec>, // Output tensor specs
    pub weight_uri: WeightUri,    // URI to immutable weights
}

#[account]
pub struct ModelInfo {
    pub id: u64,
    pub name: String,
    pub description: String,
    pub creator: String,
    pub task_ids: Vec<u64>,
    pub connections: Vec<TaskConnection>,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct TaskExecutionStatus {
    pub task_index: u64,
    pub task_id: u64,
    pub task_to_verify: Option<u64>,
    pub assigned_node: Pubkey,
    pub status: TaskExecutionState, // 0: pending, 1: assigned, 2: in-progress, 3: completed, 4: failed
    pub input_uris: Vec<TensorUri>, // URIs to input tensors
    pub output_uris: Vec<TensorUri>, // URIs to output tensors
    pub start_time: i64,
    pub completion_time: i64,
}

#[account]
pub struct ModelExecution {
    pub id: u64,
    pub model_id: u64,
    pub requestor: Pubkey,
    pub fee: u64,
    pub task_statuses: Vec<TaskExecutionStatus>,
    pub overall_status: TaskExecutionState, // 0: pending, 1: in-progress, 2: completed, 3: failed
    pub input_uri: TensorUri,               // Initial model input
    pub output_uri: TensorUri,              // Final model output
    pub start_time: i64,
    pub completion_time: i64,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct NodeSpecialization {
    pub task_id: u64,
}

#[account]
pub struct NodeInfo {
    pub owner: Pubkey,
    pub stake_amount: u64,
    pub specializations: Vec<NodeSpecialization>,
}

#[account]
pub struct AdminConfig {
    pub admin: Pubkey,
}

// Constants and Implementations
impl ModelInfo {
    pub const MAX_TASKS: usize = 16;
    pub const MAX_CONNECTIONS: usize = 64;
    pub const MAX_NAME_LEN: usize = 64;
    pub const MAX_DESC_LEN: usize = 256;
    pub const MAX_CREATOR_LEN: usize = 64;
    pub const MAX_SIZE: usize = 8 + // id
        (4 + Self::MAX_NAME_LEN) +
        (4 + Self::MAX_DESC_LEN) +
        (4 + Self::MAX_CREATOR_LEN) +
        (4 + Self::MAX_TASKS * 8) +
        (4 + Self::MAX_CONNECTIONS * TaskConnection::MAX_SIZE);
}

impl NodeInfo {
    pub const MAX_SPECIALIZATIONS: usize = 32;
    pub const MAX_SIZE: usize = 32 + // owner
        8 + // stake_amount
        (4 + Self::MAX_SPECIALIZATIONS * NodeSpecialization::MAX_SIZE);
}

impl TaskInfo {
    pub const MAX_INPUTS: usize = 8;
    pub const MAX_OUTPUTS: usize = 8;
    pub const MAX_DESC_LEN: usize = 256;
    pub const MAX_WEIGHT_URI_LEN: usize = 128;
    pub const MAX_SIZE: usize = 8 + // id
        8 + // model_id
        (4 + Self::MAX_DESC_LEN) +
        8 + // vram_requirement
        8 + // compute_units
        (4 + Self::MAX_INPUTS * TensorSpec::MAX_SIZE) +
        (4 + Self::MAX_OUTPUTS * TensorSpec::MAX_SIZE) +
        (4 + Self::MAX_WEIGHT_URI_LEN);
}

impl TaskConnection {
    pub const MAX_SIZE: usize = 8 + 8 + 8 + 8 + TensorSpec::MAX_SIZE;
}

impl TensorSpec {
    pub const MAX_NAME_LEN: usize = 32;
    pub const MAX_DIMENSIONS: usize = 8;
    pub const MAX_SHAPE: usize = 8;
    pub const MAX_DTYPE_LEN: usize = 16;
    pub const MAX_SIZE: usize = (4 + Self::MAX_NAME_LEN) + // name
        (4 + Self::MAX_DIMENSIONS * 32) + // dimensions (String array)
        1 + (4 + Self::MAX_SHAPE * 8) + // Optional shape (u64 array)
        (4 + Self::MAX_DTYPE_LEN); // dtype
}

impl NodeSpecialization {
    pub const MAX_SIZE: usize = 8; // task_id
}

// Input Structures
#[derive(AnchorSerialize, AnchorDeserialize)]
pub struct ModelInfoInput {
    pub id: u64,
    pub name: String,
    pub description: String,
    pub creator: String,
    pub task_ids: Vec<u64>,
    pub connections: Vec<TaskConnection>,
}

#[derive(AnchorSerialize, AnchorDeserialize)]
pub struct NodeInfoInput {
    pub stake_amount: u64,
    pub specializations: Vec<NodeSpecialization>,
}

#[derive(AnchorSerialize, AnchorDeserialize)]
pub struct TaskInfoInput {
    pub id: u64,
    pub model_id: u64,
    pub description: String,
    pub vram_requirement: u64,
    pub compute_units: u64,
    pub inputs: Vec<TensorSpec>,
    pub outputs: Vec<TensorSpec>,
    pub weight_uri: WeightUri,
}

// Conversions
impl From<ModelInfoInput> for ModelInfo {
    fn from(input: ModelInfoInput) -> Self {
        ModelInfo {
            id: input.id,
            name: input.name,
            description: input.description,
            creator: input.creator,
            task_ids: input.task_ids,
            connections: input.connections,
        }
    }
}

impl From<NodeInfoInput> for NodeInfo {
    fn from(input: NodeInfoInput) -> Self {
        NodeInfo {
            owner: Pubkey::default(), // Will be set in instruction
            stake_amount: input.stake_amount,
            specializations: input.specializations,
        }
    }
}

impl From<TaskInfoInput> for TaskInfo {
    fn from(input: TaskInfoInput) -> Self {
        TaskInfo {
            id: input.id,
            model_id: input.model_id,
            description: input.description,
            vram_requirement: input.vram_requirement,
            compute_units: input.compute_units,
            inputs: input.inputs,
            outputs: input.outputs,
            weight_uri: input.weight_uri,
        }
    }
}

impl ModelExecution {
    pub const MAX_TASKS: usize = 16;
    pub const MAX_URI_LEN: usize = 128;
    pub const MAX_SIZE: usize = 8 + // id
        8 + // model_id
        32 + // requestor (Pubkey)
        8 + // fee
        (4 + Self::MAX_TASKS * TaskExecutionStatus::MAX_SIZE) + // task_statuses
        1 + // overall_status
        (4 + Self::MAX_URI_LEN) + // input_uri
        (4 + Self::MAX_URI_LEN) + // output_uri
        8 + // start_time
        8; // completion_time
}

impl TaskExecutionStatus {
    pub const MAX_URIS: usize = 8;
    pub const MAX_URI_LEN: usize = 128;
    pub const MAX_SIZE: usize = 8 + // task_id
        32 + // assigned_node (Pubkey)
        1 + // status
        (4 + Self::MAX_URIS * (4 + Self::MAX_URI_LEN)) + // input_uris
        (4 + Self::MAX_URIS * (4 + Self::MAX_URI_LEN)) + // output_uris
        8 + // start_time
        8; // completion_time
}

impl OracleCommittee {
    pub const MAX_MEMBERS: usize = 32;
    pub const MAX_SIZE: usize = 4 + // vec length prefix
        (Self::MAX_MEMBERS * 32); // members (array of Pubkeys)
}

impl AdminConfig {
    pub const SEED_PREFIX: &'static [u8] = b"admin";
    pub const SPACE: usize = 8 + // discriminator
        32; // admin pubkey
}
