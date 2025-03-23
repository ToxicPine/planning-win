# cli/commands.py
import click
from pydantic import ValidationError
from .models import NodeRegistration, NodeSpecialization
from .config import settings

@click.group()
def cli():
    """SplitUp Node Management CLI."""
    pass

@cli.command()
@click.option('--stake-amount', required=True, type=int, help='Amount to stake')
def register(stake_amount):
    """Register a node with the SplitUp network."""
    try:
        data = NodeRegistration(stake_amount=stake_amount)
        # Add logic to register node, e.g., call underlying service
        click.echo(f"Registering node with stake: {data.stake_amount}")
    except ValidationError as e:
        click.echo(f"Validation error: {e}")
        raise SystemExit(1)

@cli.command()
@click.option('--model-id', required=True, type=str, help='Model identifier (e.g. llama-70b)')
@click.option('--tasks', required=True, type=str, help='Comma-separated list of task IDs')
def specialize(model_id, tasks):
    """Specialize a node in specific tasks."""
    try:
        data = NodeSpecialization(model_id=model_id, tasks=tasks)
        # Add logic to specialize node based on validated input
        click.echo(f"Specializing node for model {data.model_id} with tasks: {data.tasks}")
    except ValidationError as e:
        click.echo(f"Validation error: {e}")
        raise SystemExit(1)

@cli.command()
@click.option('--model-id', required=True, type=str, help='Model identifier')
@click.option('--tasks', required=True, type=str, help='Comma-separated list of task IDs')
def preload(model_id, tasks):
    """Preload model weights for performance."""
    try:
        data = NodeSpecialization(model_id=model_id, tasks=tasks)
        # Add logic to preload model weights
        click.echo(f"Preloading weights for model {data.model_id} on tasks: {data.tasks}")
    except ValidationError as e:
        click.echo(f"Validation error: {e}")
        raise SystemExit(1)

@cli.command()
def start():
    """Start all node services."""
    # Implement logic to start services (heartbeat, listener, compute)
    click.echo("Starting node services...")

@cli.command()
def status():
    """Check current node status."""
    # Implement logic to retrieve node status
    click.echo("Fetching node status...")

if __name__ == '__main__':
    cli()
