# cli/commands.py
import click
import time
import random
from pydantic import ValidationError
from .models import NodeRegistration, NodeSpecialization, ModelRegistration, ModelExecution
from .config import settings
from .services import ComputeServiceClient

LATTICE_LOGO = """
██▓    ▄▄▄     ▄▄▄█████▓▄▄▄█████▓ ██▓ ▄████▄  ▓█████ 
▓██▒   ▒████▄   ▓  ██▒ ▓▒▓  ██▒ ▓▒▓██▒▒██▀ ▀█  ▓█   ▀ 
▒██░   ▒██  ▀█▄ ▒ ▓██░ ▒░▒ ▓██░ ▒░▒██▒▒▓█    ▄ ▒███   
▒██░   ░██▄▄▄▄██░ ▓██▓ ░ ░ ▓██▓ ░ ░██░▒▓▓▄ ▄██▒▒▓█  ▄ 
░██████▒▓█   ▓██▒ ▒██▒ ░   ▒██▒ ░ ░██░▒ ▓███▀ ░░▒████▒
░ ▒░▓  ░▒▒   ▓▒█░ ▒ ░░     ▒ ░░   ░▓  ░ ░▒ ▒  ░░░ ▒░ ░
░ ░ ▒  ░ ▒   ▒▒ ░   ░        ░     ▒ ░  ░  ▒    ░ ░  ░
  ░ ░    ░   ▒    ░        ░       ▒ ░░           ░   
    ░  ░     ░  ░                  ░  ░ ░         ░  ░
                                      ░
"""

def print_header():
    """Print the Lattice logo and header."""
    click.echo(click.style(LATTICE_LOGO, fg="red"))
    click.echo(click.style("=" * 80, fg="blue"))
    click.echo(click.style("SplitUp Node Management CLI", fg="green", bold=True))
    click.echo(click.style("=" * 80, fg="blue"))
    click.echo()

def simulate_network_delay():
    """Simulate network delay for more realistic feel."""
    time.sleep(random.uniform(0.5, 1.5))

@click.group()
def cli():
    """SplitUp Node Management CLI."""
    print_header()
    simulate_network_delay()

# Node Management Commands
@cli.group()
def node():
    """Node management commands."""
    click.echo(click.style("\nNode Management", fg="yellow", bold=True))
    click.echo(click.style("-" * 40, fg="yellow"))
    simulate_network_delay()

@node.command()
def register():
    """Register a node with the SplitUp network."""
    try:
        with click.progressbar(length=100, label="Initializing node registration") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)

        data = NodeRegistration(stake_amount=settings.SPLITUP_NODE_STAKE_AMOUNT)
        click.echo(click.style("\nNode Registration", fg="green", bold=True))
        click.echo(click.style(f"Stake Amount: ${data.stake_amount}", fg="white"))
        
        with click.progressbar(length=100, label="Processing registration") as bar:
            for _ in range(20):
                time.sleep(0.2)
                bar.update(5)

        click.echo(click.style("Status: ", fg="yellow") + click.style("Processing...", fg="cyan"))
        
        with click.progressbar(length=100, label="Finalizing registration") as bar:
            for _ in range(20):
                time.sleep(0.15)
                bar.update(5)

        click.echo(click.style("✓ Node registered successfully!", fg="green"))
        click.echo(click.style(f"Node ID: node-{random.randint(1000, 9999)}", fg="white"))
        click.echo(click.style(f"Registration Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", fg="white"))
    except ValidationError as e:
        click.echo(click.style(f"✗ Validation error: {e}", fg="red"))
        raise SystemExit(1)

@node.command()
@click.option('--model-id', required=True, type=str, help='Model identifier (e.g. llama-70b)')
@click.option('--tasks', required=True, type=str, help='Comma-separated list of task IDs')
def specialize(model_id, tasks):
    """Specialize a node in specific tasks."""
    try:
        if not model_id or not tasks:
            click.echo(click.style("✗ Model ID and tasks cannot be empty", fg="red"))
            raise SystemExit(1)

        with click.progressbar(length=100, label="Validating model and tasks") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)

        data = NodeSpecialization(model_id=model_id, tasks=tasks.split(','))
        click.echo(click.style("\nNode Specialization", fg="green", bold=True))
        click.echo(click.style(f"Model ID: {data.model_id}", fg="white"))
        click.echo(click.style("Tasks:", fg="white"))
        for task in data.tasks:
            click.echo(click.style(f"  • {task}", fg="cyan"))

        with click.progressbar(length=100, label="Configuring node for tasks") as bar:
            for _ in range(20):
                time.sleep(0.2)
                bar.update(5)

        click.echo(click.style("Status: ", fg="yellow") + click.style("Processing...", fg="cyan"))
        
        with click.progressbar(length=100, label="Finalizing specialization") as bar:
            for _ in range(20):
                time.sleep(0.15)
                bar.update(5)

        click.echo(click.style("✓ Node specialized successfully!", fg="green"))
        click.echo(click.style(f"Specialization Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", fg="white"))
    except ValidationError as e:
        click.echo(click.style(f"✗ Validation error: {e}", fg="red"))
        raise SystemExit(1)

@node.command()
@click.option('--model-id', required=True, type=str, help='Model identifier')
@click.option('--tasks', required=True, type=str, help='Comma-separated list of task IDs')
def preload(model_id, tasks):
    """Preload model weights for performance."""
    try:
        data = NodeSpecialization(model_id=model_id, tasks=tasks.split(','))
        click.echo(click.style("\nModel Preloading", fg="green", bold=True))
        click.echo(click.style(f"Model ID: {data.model_id}", fg="white"))
        click.echo(click.style("Tasks:", fg="white"))
        for task in data.tasks:
            click.echo(click.style(f"  • {task}", fg="cyan"))

        with click.progressbar(length=100, label="Initializing preload") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)

        click.echo(click.style("Status: ", fg="yellow") + click.style("Preloading weights...", fg="cyan"))
        
        with click.progressbar(length=100, label="Loading model weights") as bar:
            for _ in range(20):
                time.sleep(0.3)
                bar.update(5)

        with click.progressbar(length=100, label="Optimizing memory") as bar:
            for _ in range(20):
                time.sleep(0.2)
                bar.update(5)

        click.echo(click.style("✓ Weights preloaded successfully!", fg="green"))
        click.echo(click.style(f"Memory Usage: {random.randint(40, 80)}%", fg="white"))
        click.echo(click.style(f"Preload Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", fg="white"))
    except ValidationError as e:
        click.echo(click.style(f"✗ Validation error: {e}", fg="red"))
        raise SystemExit(1)

@node.command()
def start():
    """Start the node and begin processing tasks."""
    try:
        client = ComputeServiceClient()
        click.echo(click.style("\nNode Startup", fg="green", bold=True))
        
        with click.progressbar(length=100, label="Initializing node") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)

        click.echo(click.style("Status: ", fg="yellow") + click.style("Starting node...", fg="cyan"))
        
        with click.progressbar(length=100, label="Loading services") as bar:
            for _ in range(20):
                time.sleep(0.2)
                bar.update(5)

        result = client.execute_task("node_start")
        
        with click.progressbar(length=100, label="Finalizing startup") as bar:
            for _ in range(20):
                time.sleep(0.15)
                bar.update(5)

        click.echo(click.style("✓ Node started successfully!", fg="green"))
        click.echo(click.style(f"Details: {result}", fg="white"))
        click.echo(click.style(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", fg="white"))
    except Exception as e:
        click.echo(click.style(f"✗ Error starting node: {e}", fg="red"))
        raise SystemExit(1)

@node.command()
def status():
    """Check the status of the node."""
    try:
        client = ComputeServiceClient()
        click.echo(click.style("\nNode Status", fg="green", bold=True))
        
        with click.progressbar(length=100, label="Fetching status") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)

        health = client.get_health_status()
        
        click.echo(click.style("\nHealth Information:", fg="yellow", bold=True))
        click.echo(click.style(f"Status: {health['health']['status']}", fg="green"))
        click.echo(click.style(f"Uptime: {health['health']['uptime']} seconds", fg="white"))
        click.echo(click.style(f"Version: {health['health']['version']}", fg="white"))
        
        click.echo(click.style("\nSystem Details:", fg="yellow", bold=True))
        for key, value in health['health']['details'].items():
            click.echo(click.style(f"  • {key}: {value}", fg="cyan"))
        
        click.echo(click.style(f"\nLast Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}", fg="white"))
    except Exception as e:
        click.echo(click.style(f"✗ Error checking node status: {e}", fg="red"))
        raise SystemExit(1)

# Model Deployment Commands
@cli.group()
def model():
    """Model management commands."""
    click.echo(click.style("\nModel Management", fg="yellow", bold=True))
    click.echo(click.style("-" * 40, fg="yellow"))
    simulate_network_delay()

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
            click.echo(click.style("✗ All fields must be non-empty and target VRAM must be positive", fg="red"))
            raise SystemExit(1)

        with click.progressbar(length=100, label="Validating model configuration") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)

        data = ModelRegistration(
            model_path=model_path,
            target_vram=target_vram,
            name=name,
            description=description,
            framework=framework
        )
        
        click.echo(click.style("\nModel Registration", fg="green", bold=True))
        click.echo(click.style(f"Name: {data.name}", fg="white"))
        click.echo(click.style(f"Description: {data.description}", fg="white"))
        click.echo(click.style(f"Target VRAM: {data.target_vram}GB", fg="white"))
        click.echo(click.style(f"Framework: {data.framework}", fg="white"))
        click.echo(click.style(f"Model Path: {data.model_path}", fg="white"))

        with click.progressbar(length=100, label="Processing model registration") as bar:
            for _ in range(20):
                time.sleep(0.2)
                bar.update(5)

        click.echo(click.style("Status: ", fg="yellow") + click.style("Processing...", fg="cyan"))
        
        with click.progressbar(length=100, label="Finalizing registration") as bar:
            for _ in range(20):
                time.sleep(0.15)
                bar.update(5)

        click.echo(click.style("✓ Model registered successfully!", fg="green"))
        click.echo(click.style(f"Model ID: model-{random.randint(1000, 9999)}", fg="white"))
        click.echo(click.style(f"Registration Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", fg="white"))
    except ValidationError as e:
        click.echo(click.style(f"✗ Validation error: {e}", fg="red"))
        raise SystemExit(1)

@model.command()
@click.option('--model-id', required=True, type=str, help='Model identifier')
@click.option('--input-file', required=True, type=str, help='Path to input file')
@click.option('--output-file', type=str, help='Path to output file (optional)')
def test(model_id, input_file, output_file):
    """Test a model with the specified input file."""
    try:
        client = ComputeServiceClient()
        click.echo(click.style("\nModel Testing", fg="green", bold=True))
        click.echo(click.style(f"Model ID: {model_id}", fg="white"))
        click.echo(click.style(f"Input File: {input_file}", fg="white"))
        if output_file:
            click.echo(click.style(f"Output File: {output_file}", fg="white"))

        with click.progressbar(length=100, label="Initializing test environment") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)

        click.echo(click.style("Status: ", fg="yellow") + click.style("Running test...", fg="cyan"))
        
        with click.progressbar(length=100, label="Loading model") as bar:
            for _ in range(20):
                time.sleep(0.2)
                bar.update(5)

        parameters = [input_file]
        if output_file:
            parameters.append(output_file)
        result = client.execute_task("model_test", parameters)
        
        with click.progressbar(length=100, label="Processing results") as bar:
            for _ in range(20):
                time.sleep(0.15)
                bar.update(5)

        click.echo(click.style("✓ Test completed successfully!", fg="green"))
        click.echo(click.style(f"Result: {result}", fg="white"))
        click.echo(click.style(f"Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", fg="white"))
    except Exception as e:
        click.echo(click.style(f"✗ Error testing model: {e}", fg="red"))
        raise SystemExit(1)

if __name__ == '__main__':
    cli()
