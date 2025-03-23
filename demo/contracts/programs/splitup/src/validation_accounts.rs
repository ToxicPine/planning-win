use std::str::FromStr;

use crate::state::*;
use anchor_lang::prelude::*;

declare_id!("11111111111111111111111111111111");

// Model Registry Accounts
#[derive(Accounts)]
pub struct RegisterModel<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(
        init,
        payer = authority,
        space = ModelInfo::MAX_SIZE
    )]
    pub model: Account<'info, ModelInfo>,
    pub system_program: Program<'info, System>,
}

// Node Registry Accounts
#[derive(Accounts)]
pub struct RegisterNode<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(
        init,
        payer = authority,
        space = NodeInfo::MAX_SIZE
    )]
    pub node: Account<'info, NodeInfo>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateStake<'info> {
    #[account(mut)]
    pub node: Account<'info, NodeInfo>,
    #[account(mut)]
    pub owner: Signer<'info>,
}

// Task Registry Accounts
#[derive(Accounts)]
pub struct RegisterTask<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(
        init,
        payer = authority,
        space = TaskInfo::MAX_SIZE
    )]
    pub task: Account<'info, TaskInfo>,
    pub system_program: Program<'info, System>,
}

// Model Execution Accounts
#[derive(Accounts)]
pub struct RequestModelExecution<'info> {
    #[account(mut)]
    pub requestor: Signer<'info>,
    pub model: Account<'info, ModelInfo>,
    #[account(
        init,
        payer = requestor,
        space = ModelExecution::MAX_SIZE
    )]
    pub execution: Account<'info, ModelExecution>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct InitializeAdmin<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(
        init,
        payer = authority,
        space = AdminConfig::SPACE,
        seeds = [AdminConfig::SEED_PREFIX],
        bump
    )]
    pub admin_config: Account<'info, AdminConfig>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RegisterOracleCommittee<'info> {
    #[account(
        mut,
        constraint = authority.key() == admin_config.admin
    )]
    pub authority: Signer<'info>,
    #[account(
        seeds = [AdminConfig::SEED_PREFIX],
        bump
    )]
    pub admin_config: Account<'info, AdminConfig>,
    #[account(
        init,
        payer = authority,
        space = OracleCommittee::MAX_SIZE
    )]
    pub oracle_committee: Account<'info, OracleCommittee>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct CompleteTask<'info> {
    #[account(mut)]
    pub node: Signer<'info>,
    #[account(
        mut,
        constraint = model.id == execution.model_id
    )]
    pub model: Account<'info, ModelInfo>,
    #[account(mut)]
    pub execution: Account<'info, ModelExecution>,
    /// CHECK: Recent slot hash used for randomness
    pub recent: AccountInfo<'info>,
}

#[derive(Accounts)]
pub struct AssignTask<'info> {
    #[account(
        constraint = oracle_committee.members.contains(&authority.key())
    )]
    pub oracle_committee: Account<'info, OracleCommittee>,
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(mut)]
    pub model_execution: Account<'info, ModelExecution>,
    #[account(mut)]
    pub node: Account<'info, NodeInfo>,
}

#[derive(Accounts)]
pub struct CancelExecution<'info> {
    #[account(mut)]
    pub requestor: Signer<'info>,
    #[account(mut)]
    pub execution: Account<'info, ModelExecution>,
}
