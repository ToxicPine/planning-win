use anchor_lang::prelude::*;

declare_id!("NodeRgs1try111111111111111111111111111111111");

#[program]
pub mod node_registry {
    use super::*;

    pub fn register_node(ctx: Context<RegisterNode>, node_info: NodeInfoInput) -> Result<()> {
        let node = &mut ctx.accounts.node;
        require!(!node.initialized, NodeError::AlreadyInitialized);
        require!(node_info.stake_amount > 0, NodeError::InvalidStake);
        require!(
            !node_info.specializations.is_empty(),
            NodeError::EmptySpecialization
        );

        node.info = node_info.into();
        node.owner = ctx.accounts.owner.key();
        node.initialized = true;

        **ctx
            .accounts
            .owner
            .to_account_info()
            .try_borrow_mut_lamports()? -= node.info.stake_amount;
        **ctx
            .accounts
            .node
            .to_account_info()
            .try_borrow_mut_lamports()? += node.info.stake_amount;

        Ok(())
    }

    pub fn stake_collateral(ctx: Context<UpdateStake>, amount: u64) -> Result<()> {
        let node = &mut ctx.accounts.node;
        require!(
            node.owner == ctx.accounts.owner.key(),
            NodeError::Unauthorized
        );
        require!(amount > 0, NodeError::InvalidStake);

        **ctx
            .accounts
            .owner
            .to_account_info()
            .try_borrow_mut_lamports()? -= amount;
        **ctx
            .accounts
            .node
            .to_account_info()
            .try_borrow_mut_lamports()? += amount;

        node.info.stake_amount = node
            .info
            .stake_amount
            .checked_add(amount)
            .ok_or(NodeError::StakeOverflow)?;
        Ok(())
    }

    pub fn withdraw_collateral(ctx: Context<UpdateStake>, amount: u64) -> Result<()> {
        let node = &mut ctx.accounts.node;
        require!(
            node.owner == ctx.accounts.owner.key(),
            NodeError::Unauthorized
        );
        require!(
            node.info.stake_amount >= amount,
            NodeError::InsufficientStake
        );

        **ctx
            .accounts
            .node
            .to_account_info()
            .try_borrow_mut_lamports()? -= amount;
        **ctx
            .accounts
            .owner
            .to_account_info()
            .try_borrow_mut_lamports()? += amount;

        node.info.stake_amount -= amount;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct RegisterNode<'info> {
    #[account(init, payer = owner, space = 8 + Node::MAX_SIZE)]
    pub node: Account<'info, Node>,
    #[account(mut)]
    pub owner: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateStake<'info> {
    #[account(mut)]
    pub node: Account<'info, Node>,
    #[account(mut)]
    pub owner: Signer<'info>,
}

#[account]
pub struct Node {
    pub owner: Pubkey,
    pub info: NodeInfo,
    pub initialized: bool,
}

impl Node {
    pub const MAX_SPECIALIZATIONS: usize = 32;
    pub const MAX_SIZE: usize = 32 + 1 + NodeInfo::MAX_SIZE;
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct NodeInfo {
    pub stake_amount: u64,
    pub specializations: Vec<NodeSpecialization>,
}

impl NodeInfo {
    pub const MAX_SIZE: usize = 8 + (4 + Node::MAX_SPECIALIZATIONS * NodeSpecialization::MAX_SIZE);
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct NodeSpecialization {
    pub task_id: u64,
}

impl NodeSpecialization {
    pub const MAX_SIZE: usize = 8;
}

#[derive(AnchorSerialize, AnchorDeserialize)]
pub struct NodeInfoInput {
    pub stake_amount: u64,
    pub specializations: Vec<NodeSpecialization>,
}

impl From<NodeInfoInput> for NodeInfo {
    fn from(input: NodeInfoInput) -> Self {
        NodeInfo {
            stake_amount: input.stake_amount,
            specializations: input.specializations,
        }
    }
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
