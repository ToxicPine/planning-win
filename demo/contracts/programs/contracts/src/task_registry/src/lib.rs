use anchor_lang::prelude::*;

declare_id!("TaskRgs1try111111111111111111111111111111111");

#[program]
pub mod task_registry {
    use super::*;

    pub fn register_task(ctx: Context<RegisterTask>, task_info: TaskInfoInput) -> Result<()> {
        let task_account = &mut ctx.accounts.task;
        require!(!task_account.initialized, TaskError::AlreadyInitialized);

        validate_tensor_specs(&task_info.inputs)?;
        validate_tensor_specs(&task_info.outputs)?;
        validate_weight_uri(&task_info.weight_uri)?;

        task_account.info = task_info.into();
        task_account.initialized = true;

        Ok(())
    }
}

#[derive(Accounts)]
pub struct RegisterTask<'info> {
    #[account(init, payer = user, space = 8 + Task::MAX_SIZE)]
    pub task: Account<'info, Task>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct Task {
    pub info: TaskInfo,
    pub initialized: bool,
}

impl Task {
    pub const MAX_INPUTS: usize = 8;
    pub const MAX_OUTPUTS: usize = 8;
    pub const MAX_DESC_LEN: usize = 256;
    pub const MAX_WEIGHT_URI_LEN: usize = 128;

    pub const MAX_SIZE: usize = 1 + TaskInfo::MAX_SIZE;
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

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct TensorSpec {
    pub dtype: u8,
    pub shape: Vec<u64>,
    pub uri: String,
}

impl TensorSpec {
    pub const MAX_SHAPE_LEN: usize = 8;
    pub const MAX_URI_LEN: usize = 128;

    pub const MAX_SIZE: usize = 1 + 4 + (8 * Self::MAX_SHAPE_LEN) + (4 + Self::MAX_URI_LEN);
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

fn validate_tensor_specs(tensors: &Vec<TensorSpec>) -> Result<()> {
    require!(!tensors.is_empty(), TaskError::EmptyTensorSpec);
    for tensor in tensors {
        require!(!tensor.shape.is_empty(), TaskError::InvalidShape);
        require!(!tensor.uri.is_empty(), TaskError::MissingTensorUri);
    }
    Ok(())
}

fn validate_weight_uri(uri: &str) -> Result<()> {
    require!(!uri.is_empty(), TaskError::MissingWeightUri);
    Ok(())
}

#[error_code]
pub enum TaskError {
    #[msg("Task already initialized")]
    AlreadyInitialized,
    #[msg("Empty tensor specification")]
    EmptyTensorSpec,
    #[msg("Invalid tensor shape")]
    InvalidShape,
    #[msg("Missing tensor URI")]
    MissingTensorUri,
    #[msg("Missing weight URI")]
    MissingWeightUri,
}
