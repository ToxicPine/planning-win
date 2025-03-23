use anchor_lang::prelude::*;
use std::collections::BTreeMap;

declare_id!("11111111111111111111111111111111");

#[program]
pub mod model_execution {
    use super::*;

    pub fn request_model_execution(
        ctx: Context<RequestExecution>,
        model_id: u64,
        input_uri: String,
        max_fee: u64,
    ) -> Result<()> {
        let exec = &mut ctx.accounts.execution;
        exec.user = ctx.accounts.user.key();
        exec.model_id = model_id;
        exec.input_uri = input_uri;
        exec.max_fee = max_fee;
        exec.status = ExecutionStatus::Requested;
        exec.assigned_tasks = vec![];
        exec.completed_tasks = vec![];
        exec.start_time = Clock::get()?.unix_timestamp;
        Ok(())
    }

    pub fn assign_task(ctx: Context<AssignTask>, task_id: u64, node: Pubkey) -> Result<()> {
        let exec = &mut ctx.accounts.execution;
        require!(
            exec.status == ExecutionStatus::Requested,
            ExecutionError::InvalidStatus
        );
        exec.assigned_tasks.push(TaskAssignment { task_id, node });
        Ok(())
    }

    pub fn report_task_completion(
        ctx: Context<ReportTaskCompletion>,
        task_id: u64,
        output_uris: Vec<String>,
    ) -> Result<()> {
        let exec = &mut ctx.accounts.execution;
        let signer = ctx.accounts.node.key();

        let task = exec.assigned_tasks.iter().find(|t| t.task_id == task_id);
        require!(task.is_some(), ExecutionError::TaskNotAssigned);
        require!(task.unwrap().node == signer, ExecutionError::Unauthorized);

        exec.completed_tasks.push(TaskResult {
            task_id,
            output_uris,
        });

        // Optional: Transition to completed if all assigned tasks done
        if exec.assigned_tasks.len() == exec.completed_tasks.len() {
            exec.status = ExecutionStatus::Completed;
        }

        Ok(())
    }

    pub fn cancel_execution(ctx: Context<CancelExecution>) -> Result<()> {
        let exec = &mut ctx.accounts.execution;
        require!(
            exec.user == ctx.accounts.user.key(),
            ExecutionError::Unauthorized
        );
        require!(
            matches!(
                exec.status,
                ExecutionStatus::Requested | ExecutionStatus::InProgress
            ),
            ExecutionError::InvalidStatus
        );
        exec.status = ExecutionStatus::Canceled;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct RequestExecution<'info> {
    #[account(init, payer = user, space = 8 + Execution::MAX_SIZE)]
    pub execution: Account<'info, Execution>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct AssignTask<'info> {
    #[account(mut)]
    pub execution: Account<'info, Execution>,
    pub oracle: Signer<'info>, // Require authority check in production
}

#[derive(Accounts)]
pub struct ReportTaskCompletion<'info> {
    #[account(mut)]
    pub execution: Account<'info, Execution>,
    pub node: Signer<'info>,
}

#[derive(Accounts)]
pub struct CancelExecution<'info> {
    #[account(mut)]
    pub execution: Account<'info, Execution>,
    #[account(mut)]
    pub user: Signer<'info>,
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

impl Execution {
    pub const MAX_TASKS: usize = 16;
    pub const MAX_URI_LEN: usize = 128;
    pub const MAX_SIZE: usize = 32 + 8 + (4 + Self::MAX_URI_LEN) + 8 + 8 +
        1 + // status
        (4 + Self::MAX_TASKS * TaskAssignment::MAX_SIZE) +
        (4 + Self::MAX_TASKS * TaskResult::MAX_SIZE);
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub enum ExecutionStatus {
    Requested,
    InProgress,
    Completed,
    Canceled,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct TaskAssignment {
    pub task_id: u64,
    pub node: Pubkey,
}

impl TaskAssignment {
    pub const MAX_SIZE: usize = 8 + 32;
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct TaskResult {
    pub task_id: u64,
    pub output_uris: Vec<String>,
}

impl TaskResult {
    pub const MAX_OUTPUTS: usize = 8;
    pub const MAX_URI_LEN: usize = 128;
    pub const MAX_SIZE: usize = 8 + 4 + (Self::MAX_OUTPUTS * (4 + Self::MAX_URI_LEN));
}

#[error_code]
pub enum ExecutionError {
    #[msg("Invalid execution status")]
    InvalidStatus,
    #[msg("Task not assigned")]
    TaskNotAssigned,
    #[msg("Unauthorized caller")]
    Unauthorized,
}
