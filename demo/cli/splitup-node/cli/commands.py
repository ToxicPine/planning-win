# cli/commands.py
import click
import time
from pydantic import ValidationError
from .models import NodeRegistration, NodeSpecialization, ModelRegistration, ModelExecution
from .config import settings
from .services import ComputeServiceClient

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
        if not model_id or not tasks:
            click.echo("Model ID and tasks cannot be empty")
            raise SystemExit(1)
        data = NodeSpecialization(model_id=model_id, tasks=tasks.split(','))
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
        data = NodeSpecialization(model_id=model_id, tasks=tasks.split(','))
        # Add logic to preload model weights
        click.echo(f"Preloading weights for model {data.model_id} on tasks: {data.tasks}")
    except ValidationError as e:
        click.echo(f"Validation error: {e}")
        raise SystemExit(1)

@node.command()
def start():
    """Start the node and begin processing tasks."""
    try:
        client = ComputeServiceClient()
        result = client.execute_task("node_start")
        click.echo(f"Node started successfully: {result}")
    except Exception as e:
        click.echo(f"Error starting node: {e}")
        raise SystemExit(1)

@node.command()
def status():
    """Check the status of the node."""
    try:
        client = ComputeServiceClient()
        health = client.get_health_status()
        click.echo(f"Node status: {health['health']['status']}")
        click.echo(f"Uptime: {health['health']['uptime']} seconds")
        click.echo(f"Version: {health['health']['version']}")
        click.echo("Details:")
        for key, value in health['health']['details'].items():
            click.echo(f"  {key}: {value}")
    except Exception as e:
        click.echo(f"Error checking node status: {e}")
        raise SystemExit(1)

# Model Deployment Commands
@cli.group()
def model():
    """Model management commands."""
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
        if not all([model_path, name, description, framework]) or target_vram <= 0:
            click.echo("All fields must be non-empty and target VRAM must be positive")
            raise SystemExit(1)
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
    """Test a model with the specified input file."""
    try:
        client = ComputeServiceClient()
        parameters = [input_file]
        if output_file:
            parameters.append(output_file)
        result = client.execute_task("model_test", parameters)
        click.echo(f"Model test started: {result}")
    except Exception as e:
        click.echo(f"Error testing model: {e}")
        raise SystemExit(1)

if __name__ == '__main__':
    cli()
