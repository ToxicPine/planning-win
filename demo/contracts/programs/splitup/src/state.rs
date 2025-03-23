use anchor_lang::prelude::*;

// State Structures
#[account]
pub struct Model {
    pub info: ModelInfo,
    pub initialized: bool,
}

#[account]
pub struct Node {
    pub owner: Pubkey,
    pub info: NodeInfo,
    pub initialized: bool,
}

#[account]
pub struct Task {
    pub info: TaskInfo,
    pub initialized: bool,
}

#[account]
pub struct Execution {
    pub user: Pubkey,
    pub model_id: u64,
    pub input_uri: String,
    pub max_fee: u64,
    pub start_time: i64,
    pub status: ExecutionStatus,
    pub assigned_tasks: Vec<TaskAssignment>,
    pub completed_tasks: Vec<TaskResult>,
}

// Supporting Structures
#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct ModelInfo {
    pub id: u64,
    pub name: String,
    pub description: String,
    pub creator: String,
    pub task_ids: Vec<u64>,
    pub connections: Vec<TaskConnection>,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct NodeInfo {
    pub stake_amount: u64,
    pub specializations: Vec<NodeSpecialization>,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct TaskInfo {
    pub id: u64,
    pub model_id: u64,
    pub description: String,
    pub vram_requirement: u32,
    pub compute_units: u32,
    pub inputs: Vec<TensorSpec>,
    pub outputs: Vec<TensorSpec>,
    pub weight_uri: String,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct TaskConnection {
    pub source_task_id: u64,
    pub destination_task_id: u64,
    pub source_output_index: u8,
    pub dest_input_index: u8,
    pub tensor_spec: TensorSpec,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct TensorSpec {
    pub dtype: u8,
    pub shape: Vec<u64>,
    pub uri: String,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct NodeSpecialization {
    pub task_id: u64,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct TaskAssignment {
    pub task_id: u64,
    pub node: Pubkey,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct TaskResult {
    pub task_id: u64,
    pub output_uris: Vec<String>,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub enum ExecutionStatus {
    Requested,
    InProgress,
    Completed,
    Canceled,
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
    pub vram_requirement: u32,
    pub compute_units: u32,
    pub inputs: Vec<TensorSpec>,
    pub outputs: Vec<TensorSpec>,
    pub weight_uri: String,
}

// Constants and Implementations
impl Model {
    pub const MAX_TASKS: usize = 16;
    pub const MAX_CONNECTIONS: usize = 64;
    pub const MAX_NAME_LEN: usize = 64;
    pub const MAX_DESC_LEN: usize = 256;
    pub const MAX_CREATOR_LEN: usize = 64;
    pub const MAX_SIZE: usize = 1 + ModelInfo::MAX_SIZE;
}

impl Node {
    pub const MAX_SPECIALIZATIONS: usize = 32;
    pub const MAX_SIZE: usize = 32 + 1 + NodeInfo::MAX_SIZE;
}

impl Task {
    pub const MAX_INPUTS: usize = 8;
    pub const MAX_OUTPUTS: usize = 8;
    pub const MAX_DESC_LEN: usize = 256;
    pub const MAX_WEIGHT_URI_LEN: usize = 128;
    pub const MAX_SIZE: usize = 1 + TaskInfo::MAX_SIZE;
}

impl Execution {
    pub const MAX_TASKS: usize = 16;
    pub const MAX_URI_LEN: usize = 128;
    pub const MAX_SIZE: usize = 32 + 8 + (4 + Self::MAX_URI_LEN) + 8 + 8 +
        1 + // status
        (4 + Self::MAX_TASKS * TaskAssignment::MAX_SIZE) +
        (4 + Self::MAX_TASKS * TaskResult::MAX_SIZE);
}

impl ModelInfo {
    pub const MAX_SIZE: usize = 8
        + (4 + Model::MAX_NAME_LEN)
        + (4 + Model::MAX_DESC_LEN)
        + (4 + Model::MAX_CREATOR_LEN)
        + (4 + Model::MAX_TASKS * 8)
        + (4 + Model::MAX_CONNECTIONS * TaskConnection::MAX_SIZE);
}

impl NodeInfo {
    pub const MAX_SIZE: usize = 8 + (4 + Node::MAX_SPECIALIZATIONS * NodeSpecialization::MAX_SIZE);
}

impl TaskInfo {
    pub const MAX_SIZE: usize = 8
        + 8
        + (4 + Task::MAX_DESC_LEN)
        + 4
        + 4
        + (4 + Task::MAX_INPUTS * TensorSpec::MAX_SIZE)
        + (4 + Task::MAX_OUTPUTS * TensorSpec::MAX_SIZE)
        + (4 + Task::MAX_WEIGHT_URI_LEN);
}

impl TaskConnection {
    pub const MAX_SIZE: usize = 8 + 8 + 1 + 1 + TensorSpec::MAX_SIZE;
}

impl TensorSpec {
    pub const MAX_SHAPE_LEN: usize = 8;
    pub const MAX_URI_LEN: usize = 128;
    pub const MAX_SIZE: usize = 1 + 4 + (8 * Self::MAX_SHAPE_LEN) + (4 + Self::MAX_URI_LEN);
}

impl NodeSpecialization {
    pub const MAX_SIZE: usize = 8;
}

impl TaskAssignment {
    pub const MAX_SIZE: usize = 8 + 32;
}

impl TaskResult {
    pub const MAX_OUTPUTS: usize = 8;
    pub const MAX_URI_LEN: usize = 128;
    pub const MAX_SIZE: usize = 8 + 4 + (Self::MAX_OUTPUTS * (4 + Self::MAX_URI_LEN));
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
