use anchor_lang::prelude::*;
use anchor_lang::system_program::ID;

declare_id!("11111111111111111111111111111111");

#[program]
pub mod model_registry {
    use super::*;

    pub fn register_model(ctx: Context<RegisterModel>, model_info: ModelInfoInput) -> Result<()> {
        let model_account = &mut ctx.accounts.model;
        require!(!model_account.initialized, ModelError::AlreadyInitialized);

        // Perform validation
        validate_model_dependencies(&model_info)?;
        validate_task_interfaces(&model_info)?;

        model_account.info = model_info.into();
        model_account.initialized = true;

        Ok(())
    }
}

#[derive(Accounts)]
pub struct RegisterModel<'info> {
    #[account(init, payer = user, space = 8 + Model::MAX_SIZE)]
    pub model: Account<'info, Model>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct Model {
    pub info: ModelInfo,
    pub initialized: bool,
}

impl Model {
    pub const MAX_TASKS: usize = 16;
    pub const MAX_CONNECTIONS: usize = 64;
    pub const MAX_NAME_LEN: usize = 64;
    pub const MAX_DESC_LEN: usize = 256;
    pub const MAX_CREATOR_LEN: usize = 64;

    pub const MAX_SIZE: usize = 1 + ModelInfo::MAX_SIZE;
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct ModelInfo {
    pub id: u64,
    pub name: String,
    pub description: String,
    pub creator: String,
    pub task_ids: Vec<u64>,
    pub connections: Vec<TaskConnection>,
}

impl ModelInfo {
    pub const MAX_SIZE: usize = 8
        + (4 + Model::MAX_NAME_LEN)
        + (4 + Model::MAX_DESC_LEN)
        + (4 + Model::MAX_CREATOR_LEN)
        + (4 + Model::MAX_TASKS * 8)
        + (4 + Model::MAX_CONNECTIONS * TaskConnection::MAX_SIZE);
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct TaskConnection {
    pub source_task_id: u64,
    pub destination_task_id: u64,
    pub source_output_index: u8,
    pub dest_input_index: u8,
    pub tensor_spec: TensorSpec,
}

impl TaskConnection {
    pub const MAX_SIZE: usize = 8 + 8 + 1 + 1 + TensorSpec::MAX_SIZE;
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct TensorSpec {
    pub dtype: u8, // e.g., 0 = float32
    pub shape: Vec<u64>,
    pub uri: String,
}

impl TensorSpec {
    pub const MAX_SHAPE_LEN: usize = 8;
    pub const MAX_URI_LEN: usize = 128;

    pub const MAX_SIZE: usize = 1 + 4 + (8 * Self::MAX_SHAPE_LEN) + (4 + Self::MAX_URI_LEN);
}

#[derive(AnchorSerialize, AnchorDeserialize)]
pub struct ModelInfoInput {
    pub id: u64,
    pub name: String,
    pub description: String,
    pub creator: String,
    pub task_ids: Vec<u64>,
    pub connections: Vec<TaskConnection>,
}

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

fn validate_model_dependencies(model_info: &ModelInfoInput) -> Result<()> {
    let mut seen = std::collections::HashSet::new();
    for conn in &model_info.connections {
        require!(
            model_info.task_ids.contains(&conn.source_task_id) || conn.source_task_id == 0,
            ModelError::InvalidDependency
        );
        require!(
            model_info.task_ids.contains(&conn.destination_task_id)
                || conn.destination_task_id == 0,
            ModelError::InvalidDependency
        );
        let key = (
            conn.source_task_id,
            conn.source_output_index,
            conn.destination_task_id,
            conn.dest_input_index,
        );
        require!(!seen.contains(&key), ModelError::DuplicateConnection);
        seen.insert(key);
    }
    Ok(())
}

fn validate_task_interfaces(_model_info: &ModelInfoInput) -> Result<()> {
    // Placeholder: Extend with domain-specific shape validation
    Ok(())
}

#[error_code]
pub enum ModelError {
    #[msg("Model already initialized")]
    AlreadyInitialized,
    #[msg("Invalid task dependency")]
    InvalidDependency,
    #[msg("Duplicate task connection")]
    DuplicateConnection,
}
