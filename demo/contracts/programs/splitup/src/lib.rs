use anchor_lang::prelude::*;
use std::collections::HashSet;

pub mod state;
pub mod validation_accounts;

use state::*;
use validation_accounts::*;

declare_id!("11111111111111111111111111111111");

#[program]
pub mod splitup {
    use super::*;

    // Model Registry Instructions
    pub fn register_model(ctx: Context<RegisterModel>, model_info: ModelInfoInput) -> Result<()> {
        validate_model_dependencies(&model_info)?;
        validate_task_interfaces(&model_info)?;

        let model = &mut ctx.accounts.model;
        model.info = model_info.into();
        model.initialized = true;
        Ok(())
    }

    // Node Registry Instructions
    pub fn register_node(ctx: Context<RegisterNode>, node_info: NodeInfoInput) -> Result<()> {
        require!(
            !node_info.specializations.is_empty(),
            NodeError::EmptySpecialization
        );
        require!(node_info.stake_amount > 0, NodeError::InvalidStake);

        let node = &mut ctx.accounts.node;
        node.owner = ctx.accounts.authority.key();
        node.info = node_info.into();
        node.initialized = true;
        Ok(())
    }

    pub fn stake_collateral(ctx: Context<UpdateStake>, amount: u64) -> Result<()> {
        require!(amount > 0, NodeError::InvalidStake);

        let node_info = ctx.accounts.node.to_account_info();
        let owner_info = ctx.accounts.owner.to_account_info();

        let node = &mut ctx.accounts.node;
        require!(
            node.owner == ctx.accounts.owner.key(),
            NodeError::Unauthorized
        );

        **owner_info.try_borrow_mut_lamports()? -= amount;
        **node_info.try_borrow_mut_lamports()? += amount;

        node.info.stake_amount = node
            .info
            .stake_amount
            .checked_add(amount)
            .ok_or(NodeError::StakeOverflow)?;
        Ok(())
    }

    pub fn withdraw_collateral(ctx: Context<UpdateStake>, amount: u64) -> Result<()> {
        let node_info = ctx.accounts.node.to_account_info();
        let owner_info = ctx.accounts.owner.to_account_info();

        let node = &mut ctx.accounts.node;
        require!(
            node.owner == ctx.accounts.owner.key(),
            NodeError::Unauthorized
        );
        require!(
            node.info.stake_amount >= amount,
            NodeError::InsufficientStake
        );

        **node_info.try_borrow_mut_lamports()? -= amount;
        **owner_info.try_borrow_mut_lamports()? += amount;

        node.info.stake_amount -= amount;
        Ok(())
    }

    // Task Registry Instructions
    pub fn register_task(ctx: Context<RegisterTask>, task_info: TaskInfoInput) -> Result<()> {
        validate_tensor_specs(&task_info.inputs)?;
        validate_tensor_specs(&task_info.outputs)?;
        validate_weight_uri(&task_info.weight_uri)?;

        let task = &mut ctx.accounts.task;
        task.info = task_info.into();
        task.initialized = true;
        Ok(())
    }

    // Model Execution Instructions
    pub fn request_model_execution(
        ctx: Context<RequestModelExecution>,
        model_id: u64,
        input_uri: String,
    ) -> Result<()> {
        let execution = &mut ctx.accounts.execution;
        execution.user = ctx.accounts.user.key();
        execution.model_id = model_id;
        execution.input_uri = input_uri.clone();
        let timestamp = Clock::get()?.unix_timestamp;
        execution.start_time = timestamp;
        execution.status = ExecutionStatus::Requested;
        execution.assigned_tasks = Vec::new();
        execution.completed_tasks = Vec::new();

        emit!(ModelExecutionRequested {
            user: ctx.accounts.user.key(),
            model_id,
            input_uri,
            timestamp,
        });

        Ok(())
    }

    pub fn start_execution(ctx: Context<StartExecution>, task_id: u64) -> Result<()> {
        let execution = &mut ctx.accounts.execution;
        require!(
            execution.status == ExecutionStatus::Requested,
            SplitupError::InvalidExecutionStatus
        );

        execution.assigned_tasks.push(TaskAssignment {
            task_id,
            node: ctx.accounts.node.key(),
        });
        execution.status = ExecutionStatus::InProgress;
        Ok(())
    }

    pub fn complete_task(
        ctx: Context<CompleteTask>,
        task_id: u64,
        output_uris: Vec<String>,
    ) -> Result<()> {
        let execution = &mut ctx.accounts.execution;
        require!(
            execution.status == ExecutionStatus::InProgress,
            SplitupError::InvalidExecutionStatus
        );

        let node_key = ctx.accounts.node.key();
        let is_assigned = execution
            .assigned_tasks
            .iter()
            .any(|t| t.task_id == task_id && t.node == node_key);

        require!(is_assigned, SplitupError::TaskNotAssigned);

        execution.completed_tasks.push(TaskResult {
            task_id,
            output_uris,
        });

        // Check if all tasks are completed
        if execution.completed_tasks.len() == execution.assigned_tasks.len() {
            execution.status = ExecutionStatus::Completed;
        }

        Ok(())
    }

    pub fn cancel_execution(ctx: Context<CancelExecution>) -> Result<()> {
        let execution = &mut ctx.accounts.execution;
        require!(
            execution.user == ctx.accounts.user.key(),
            SplitupError::Unauthorized
        );
        require!(
            execution.status != ExecutionStatus::Completed,
            SplitupError::InvalidExecutionStatus
        );

        execution.status = ExecutionStatus::Canceled;
        Ok(())
    }

    pub fn get_specialized_nodes(
        ctx: Context<GetSpecializedNodes>,
        task_id: u64,
    ) -> Result<Vec<Pubkey>> {
        let mut specialized_nodes = Vec::new();

        for acc in ctx.remaining_accounts {
            let node = acc.try_borrow_data()?;
            if let Ok(node_data) = Node::try_deserialize(&mut &node[..]) {
                if node_data
                    .info
                    .specializations
                    .iter()
                    .any(|s| s.task_id == task_id)
                {
                    specialized_nodes.push(node_data.owner);
                }
            }
        }

        Ok(specialized_nodes)
    }
}

// Helper Functions
fn validate_model_dependencies(model_info: &ModelInfoInput) -> Result<()> {
    let mut seen = HashSet::new();
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
    Ok(())
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

// Error Enums
#[error_code]
pub enum ModelError {
    #[msg("Model already initialized")]
    AlreadyInitialized,
    #[msg("Invalid task dependency")]
    InvalidDependency,
    #[msg("Duplicate task connection")]
    DuplicateConnection,
}

#[error_code]
pub enum NodeError {
    #[msg("Node already initialized")]
    AlreadyInitialized,
    #[msg("Invalid stake amount")]
    InvalidStake,
    #[msg("Unauthorized action")]
    Unauthorized,
    #[msg("Empty specialization list")]
    EmptySpecialization,
    #[msg("Stake amount too large")]
    StakeOverflow,
    #[msg("Insufficient staked collateral")]
    InsufficientStake,
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

#[error_code]
pub enum SplitupError {
    #[msg("Invalid execution status")]
    InvalidExecutionStatus,
    #[msg("Task not assigned to node")]
    TaskNotAssigned,
    #[msg("Unauthorized")]
    Unauthorized,
}

#[derive(Accounts)]
pub struct GetSpecializedNodes<'info> {
    /// CHECK: This account is not written to
    pub authority: UncheckedAccount<'info>,
}

#[event]
pub struct ModelExecutionRequested {
    pub user: Pubkey,
    pub model_id: u64,
    pub input_uri: String,
    pub timestamp: i64,
}
