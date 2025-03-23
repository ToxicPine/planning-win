use crate::state::*;
use anchor_lang::prelude::*;

// Model Registry Accounts
#[derive(Accounts)]
pub struct RegisterModel<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(
        init,
        payer = authority,
        space = Model::MAX_SIZE
    )]
    pub model: Account<'info, Model>,
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
        space = Node::MAX_SIZE
    )]
    pub node: Account<'info, Node>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateStake<'info> {
    #[account(mut)]
    pub node: Account<'info, Node>,
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
        space = Task::MAX_SIZE
    )]
    pub task: Account<'info, Task>,
    pub system_program: Program<'info, System>,
}

// Model Execution Accounts
#[derive(Accounts)]
pub struct RequestModelExecution<'info> {
    #[account(mut)]
    pub user: Signer<'info>,
    #[account(
        init,
        payer = user,
        space = Execution::MAX_SIZE
    )]
    pub execution: Account<'info, Execution>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct StartExecution<'info> {
    #[account(mut)]
    pub node: Signer<'info>,
    #[account(mut)]
    pub execution: Account<'info, Execution>,
}

#[derive(Accounts)]
pub struct CompleteTask<'info> {
    #[account(mut)]
    pub node: Signer<'info>,
    #[account(mut)]
    pub execution: Account<'info, Execution>,
}

#[derive(Accounts)]
pub struct CancelExecution<'info> {
    #[account(mut)]
    pub user: Signer<'info>,
    #[account(mut)]
    pub execution: Account<'info, Execution>,
}

#[derive(Accounts)]
pub struct GetSpecializedNodes<'info> {
    pub authority: Signer<'info>,
}
