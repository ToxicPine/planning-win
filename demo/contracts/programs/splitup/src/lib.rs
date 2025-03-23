use anchor_lang::prelude::*;
use std::collections::HashMap;
use std::collections::HashSet;

pub mod state;
pub mod validation_accounts;

use state::*;
use validation_accounts::*;

declare_id!("11111111111111111111111111111111");

const MIN_STAKE: u64 = 30_000;

#[program]
pub mod splitup {
    use super::*;

    // Oracle Committee Instructions
    pub fn register_oracle_committee(
        ctx: Context<RegisterOracleCommittee>,
        members: Vec<Pubkey>,
    ) -> Result<()> {
        require!(
            members.len() <= OracleCommittee::MAX_MEMBERS,
            SplitupError::Error
        );
        let oracle_committee = &mut ctx.accounts.oracle_committee;
        oracle_committee.members = members;
        Ok(())
    }

    // Task Registry Instructions
    pub fn register_task(ctx: Context<RegisterTask>, task_info: TaskInfoInput) -> Result<()> {
        validate_tensor_specs(&task_info.inputs)?;
        validate_tensor_specs(&task_info.outputs)?;
        validate_weight_uri(&task_info.weight_uri)?;

        let task = &mut ctx.accounts.task;
        task.id = task_info.id;
        task.model_id = task_info.model_id;
        task.description = task_info.description;
        task.vram_requirement = task_info.vram_requirement;
        task.compute_units = task_info.compute_units;
        task.inputs = task_info.inputs;
        task.outputs = task_info.outputs;
        task.weight_uri = task_info.weight_uri;

        emit!(TaskRegistered {
            task_id: task.id,
            model_id: task.model_id,
            compute_units: task.compute_units as u64,
            timestamp: Clock::get()?.unix_timestamp,
        });

        Ok(())
    }

    // Model Registry Instructions
    pub fn register_model(ctx: Context<RegisterModel>, model_info: ModelInfoInput) -> Result<()> {
        validate_model_dependencies(&model_info)?;
        validate_task_interfaces(&ctx, &model_info)?;

        let model = &mut ctx.accounts.model;
        model.id = model_info.id;
        model.name = model_info.name;
        model.description = model_info.description;
        model.creator = model_info.creator;
        model.task_ids = model_info.task_ids;
        model.connections = model_info.connections;

        emit!(ModelRegistered {
            model_id: model.id,
            creator: ctx.accounts.authority.key(),
            task_ids: model.task_ids.clone(),
            timestamp: Clock::get()?.unix_timestamp,
        });

        Ok(())
    }

    // Node Registry Instructions
    pub fn register_node(
        ctx: Context<RegisterNode>,
        node_info: NodeInfoInput,
        amount: u64,
    ) -> Result<()> {
        require!(
            !node_info.specializations.is_empty(),
            NodeError::EmptySpecialization
        );
        require!(amount >= MIN_STAKE, NodeError::InvalidStake);

        let node_key = ctx.accounts.node.key();
        let node = &mut ctx.accounts.node;
        let authority_info = ctx.accounts.authority.to_account_info();
        let node_info_account = node.to_account_info();

        // Transfer the stake amount from authority to node account
        **authority_info.try_borrow_mut_lamports()? -= amount;
        **node_info_account.try_borrow_mut_lamports()? += amount;

        node.owner = ctx.accounts.authority.key();
        node.stake_amount = amount;
        node.specializations = node_info.specializations.clone();

        emit!(NodeRegistered {
            node: node_key,
            owner: node.owner,
            specializations: node_info.specializations,
            stake_amount: amount,
            timestamp: Clock::get()?.unix_timestamp,
        });

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
        require!(node.stake_amount >= amount, NodeError::InsufficientStake);

        **node_info.try_borrow_mut_lamports()? -= amount;
        **owner_info.try_borrow_mut_lamports()? += amount;

        node.stake_amount -= amount;
        Ok(())
    }

    // Model Execution Instructions
    pub fn request_model_execution(
        ctx: Context<RequestModelExecution>,
        model_id: u64,
        input_uri: String,
    ) -> Result<()> {
        let execution_key = ctx.accounts.execution.key();
        let execution = &mut ctx.accounts.execution;
        execution.requestor = ctx.accounts.requestor.key();

        let model_info = &ctx.accounts.model;

        execution.model_id = model_info.id;
        execution.input_uri = input_uri.clone();
        let timestamp = Clock::get()?.unix_timestamp;
        execution.start_time = timestamp;
        execution.overall_status = TaskExecutionState::Pending;
        execution.task_statuses = Vec::new();
        execution.id = execution_key.to_bytes()[0..8]
            .try_into()
            .map(u64::from_le_bytes)
            .unwrap();

        emit!(ModelExecutionRequested {
            requestor: ctx.accounts.requestor.key(),
            execution_id: execution.id,
            model_id,
            input_uri,
            timestamp,
        });

        // TO DO: Check if task exists in registry
        for (idx, task_id) in model_info.task_ids.iter().enumerate() {
            execution.task_statuses.push(TaskExecutionStatus {
                task_index: idx as u64,
                task_id: *task_id,
                task_to_verify: None,
                assigned_node: Pubkey::default(),
                status: TaskExecutionState::Pending,
                input_uris: Vec::new(),
                output_uris: Vec::new(),
                start_time: 0,
                completion_time: 0,
            });
        }

        emit!(RequestNodeSelection {
            execution_id: execution.id,
            requestor: ctx.accounts.requestor.key(),
            tasks: execution.task_statuses.clone(),
            timestamp,
        });

        Ok(())
    }

    pub fn assign_task(ctx: Context<AssignTask>, task_id: u64) -> Result<()> {
        // TODO: Check if task has already been assigned or not

        let model_execution = &mut ctx.accounts.model_execution;
        let node_address = ctx.accounts.node.owner;
        let idx = model_execution
            .task_statuses
            .iter()
            .position(|t| t.task_id == task_id)
            .ok_or(SplitupError::NotFound)?;
        model_execution.task_statuses[idx].assigned_node = node_address;
        model_execution.task_statuses[idx].status = TaskExecutionState::Assigned;

        emit!(TaskAssigned {
            execution_id: model_execution.id,
            task_index: idx as u64,
            node: node_address,
            timestamp: Clock::get()?.unix_timestamp,
        });

        // If all tasks are assigned, request task begin

        let is_completed = model_execution
            .task_statuses
            .iter()
            .all(|t| t.status == TaskExecutionState::Assigned);

        if is_completed {
            emit!(RequestTaskBegin {
                execution_id: model_execution.id,
                task_index: 0,
                task_execution: model_execution.task_statuses[0].clone(),
            });
        }

        Ok(())
    }

    pub fn complete_task(
        ctx: Context<CompleteTask>,
        task_index: u64,
        output_uris: Vec<String>,
    ) -> Result<()> {
        let execution = &mut ctx.accounts.execution;

        // TODO Check if task index is valid

        let idx = task_index as usize;

        // TODO: Implement the tensor comparasion with manhattan distance

        /*
        if execution.task_statuses[idx].task_to_verify.is_some() {
            execution.task_statuses[idx].status = TaskExecutionState::Completed;
        }*/
        // Pseudo random (CHANGE)
        let data = ctx.accounts.recent.to_account_info().data;
        let recent_slothash = data.borrow();
        let random_number = get_random_number(&recent_slothash);

        if random_number <= 8 {
            /*execution.task_statuses[idx].status = TaskExecutionState::PendingVerification;
            let new_task_status = execution.task_statuses[idx].clone();
            let new_idx = execution.task_statuses.len();
            execution.task_statuses.push(new_task_status);
            execution.task_statuses[new_idx].task_to_verify = Some(idx as u64);

            emit!(RequestNodeSelection {
                requestor: execution.requestor,
                execution_id: execution.id,
                tasks: vec![execution.task_statuses[new_idx].clone()],
                timestamp: Clock::get()?.unix_timestamp,
            });*/

            // PASS FOR NOW, since this will cause a new pipeline that will interfere with the current pipeline
        }

        execution.task_statuses[idx].output_uris = output_uris.clone();
        execution.task_statuses[idx].status = TaskExecutionState::Completed;

        let is_completed = execution
            .task_statuses
            .iter()
            .all(|t| t.status == TaskExecutionState::Completed);
        if is_completed {
            execution.overall_status = TaskExecutionState::Completed;
        }

        emit!(TaskCompleted {
            execution_id: execution.id,
            task_index: task_index as u64,
            task_id: execution.task_statuses[task_index as usize].task_id,
            node: ctx.accounts.node.key(),
            output_uris,
            timestamp: Clock::get()?.unix_timestamp,
        });

        if !is_completed {
            // Find first uncompleted task
            let next_task_index = ctx.accounts.model.connections[idx].destination_task_id;

            if next_task_index != 0 {
                emit!(RequestTaskBegin {
                    execution_id: execution.id,
                    task_index: next_task_index,
                    task_execution: execution.task_statuses[next_task_index as usize].clone(),
                });
            } else {
                emit!(ModelExecutionCompleted {
                    execution_id: execution.id,
                    model_id: ctx.accounts.model.id,
                    timestamp: Clock::get()?.unix_timestamp,
                });
            }
        }
        Ok(())
    }

    pub fn initialize_admin(ctx: Context<InitializeAdmin>) -> Result<()> {
        let admin_config = &mut ctx.accounts.admin_config;
        admin_config.admin = ctx.accounts.authority.key();
        Ok(())
    }
}

// Helper Functions
fn validate_tensor_specs(tensors: &Vec<TensorSpec>) -> Result<()> {
    require!(!tensors.is_empty(), TaskError::EmptyTensorSpec);
    for tensor in tensors {
        if let Some(shape) = &tensor.shape {
            require!(!shape.is_empty(), TaskError::InvalidShape);
        }
    }
    Ok(())
}

fn validate_weight_uri(uri: &str) -> Result<()> {
    require!(!uri.is_empty(), TaskError::MissingWeightUri);
    Ok(())
}

fn get_random_number(recent_slothash: &[u8]) -> u64 {
    let hash_value = u64::from_le_bytes(recent_slothash[0..8].try_into().unwrap());
    (hash_value % 100) + 1
}

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

// Validate that all tasks in the model exist and are initialized
fn validate_task_interfaces(
    ctx: &Context<RegisterModel>,
    model_info: &ModelInfoInput,
) -> Result<()> {
    // Process remaining accounts which should be Task accounts
    let task_accounts: HashMap<u64, TaskInfo> = ctx
        .remaining_accounts
        .iter()
        .filter_map(|acc| {
            let data = acc.try_borrow_data().ok()?;
            if let Ok(task) = TaskInfo::try_deserialize(&mut &data[..]) {
                Some((task.id, task))
            } else {
                None
            }
        })
        .collect();

    // Check that all task_ids in the model exist and are initialized
    for &task_id in &model_info.task_ids {
        require!(
            task_accounts.contains_key(&task_id),
            ModelError::InvalidDependency
        );
    }

    // Validate all connections reference valid tasks
    for conn in &model_info.connections {
        // Skip validation for model inputs/outputs (task_id == 0)
        if conn.source_task_id != 0 {
            require!(
                task_accounts.contains_key(&conn.source_task_id),
                ModelError::InvalidDependency
            );
        }
        if conn.destination_task_id != 0 {
            require!(
                task_accounts.contains_key(&conn.destination_task_id),
                ModelError::InvalidDependency
            );
        }
    }

    Ok(())
}

// Events
#[event]
pub struct ModelRegistered {
    pub model_id: u64,
    pub creator: Pubkey,
    pub task_ids: Vec<u64>,
    pub timestamp: i64,
}

#[event]
pub struct TaskRegistered {
    pub task_id: u64,
    pub model_id: u64,
    pub compute_units: u64,
    pub timestamp: i64,
}

#[event]
pub struct NodeRegistered {
    pub node: Pubkey,
    pub owner: Pubkey,
    pub specializations: Vec<NodeSpecialization>,
    pub stake_amount: u64,
    pub timestamp: i64,
}

#[event]
pub struct StakeUpdated {
    pub node: Pubkey,
    pub owner: Pubkey,
    pub new_amount: u64,
    pub timestamp: i64,
}

#[event]
pub struct ModelExecutionRequested {
    pub requestor: Pubkey,
    pub execution_id: u64,
    pub model_id: u64,
    pub input_uri: String,
    pub timestamp: i64,
}

#[event]
pub struct RequestNodeSelection {
    pub execution_id: u64,
    pub requestor: Pubkey,
    pub tasks: Vec<TaskExecutionStatus>,
    pub timestamp: i64,
}

#[event]
pub struct TaskAssigned {
    pub execution_id: u64,
    pub task_index: u64,
    pub node: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct TaskCompleted {
    pub execution_id: u64,
    pub task_index: u64,
    pub task_id: u64,
    pub node: Pubkey,
    pub output_uris: Vec<String>,
    pub timestamp: i64,
}

#[event]
pub struct RequestTaskBegin {
    pub execution_id: u64,
    pub task_index: u64,
    pub task_execution: TaskExecutionStatus,
}

#[event]
pub struct ModelExecutionCompleted {
    pub execution_id: u64,
    pub model_id: u64,
    pub timestamp: i64,
}

#[event]
pub struct ModelExecutionCanceled {
    pub execution_id: u64,
    pub model_id: u64,
    pub timestamp: i64,
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
    #[msg("Task deadline exceeded")]
    TaskDeadlineExceeded,
    #[msg("Not Found")]
    NotFound,
    #[msg("Error")]
    Error,
}
