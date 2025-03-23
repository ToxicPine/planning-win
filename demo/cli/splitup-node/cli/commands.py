# cli/commands.py
import click
from pydantic import ValidationError
from .models import NodeRegistration, NodeSpecialization, ModelRegistration, ModelExecution
from .config import settings

@click.group()
def cli():
    """SplitUp Node Management CLI."""
    pass

# Node Management Commands
@cli.group()
def node():
    """Node management commands."""
    pass

@node.command()
def register():
    """Register a node with the SplitUp network."""
    try:
        data = NodeRegistration(stake_amount=settings.SPLITUP_NODE_STAKE_AMOUNT)
        # Add logic to register node, e.g., call underlying service
        click.echo(f"Registering node with stake: ${data.stake_amount}")
    except ValidationError as e:
        click.echo(f"Validation error: {e}")
        raise SystemExit(1)

@node.command()
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

@node.command()
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

@node.command()
def start():
    """Start all node services."""
    # Implement logic to start services (heartbeat, listener, compute)
    click.echo("Starting node services...")

@node.command()
def status():
    """Check current node status."""
    # Implement logic to retrieve node status
    click.echo("Fetching node status...")

# Model Deployment Commands
@cli.group()
def model():
    """Model deployment commands."""
    pass

@model.command()
@click.option('--model-path', required=True, type=str, help='Path to the model file')
@click.option('--target-vram', required=True, type=int, help='Target VRAM constraint in GB')
@click.option('--name', required=True, type=str, help='Model name')
@click.option('--description', required=True, type=str, help='Model description')
@click.option('--framework', required=True, type=str, help='Model framework (e.g. tinygrad)')
def register(model_path, target_vram, name, description, framework):
    """Register a model with the SplitUp network."""
    try:
        data = ModelRegistration(
            model_path=model_path,
            target_vram=target_vram,
            name=name,
            description=description,
            framework=framework
        )
        # Add logic to register model
        click.echo(f"Registering model: {data.name}")
        click.echo(f"Target VRAM: {data.target_vram}GB")
        click.echo(f"Framework: {data.framework}")
    except ValidationError as e:
        click.echo(f"Validation error: {e}")
        raise SystemExit(1)

@model.command()
@click.option('--model-id', required=True, type=str, help='Model identifier')
@click.option('--input-file', required=True, type=str, help='Path to input file')
@click.option('--output-file', type=str, help='Path to output file (optional)')
def test(model_id, input_file, output_file):
    """Test model execution on the network."""
    try:
        data = ModelExecution(
            model_id=model_id,
            input_file=input_file,
            output_file=output_file
        )
        # Add logic to test model execution
        click.echo(f"Testing model execution for {data.model_id}")
        click.echo(f"Input file: {data.input_file}")
        click.echo(f"Output file: {data.output_file if data.output_file else 'None'}")
    except ValidationError as e:
        click.echo(f"Validation error: {e}")
        raise SystemExit(1)

if __name__ == '__main__':
    cli()
