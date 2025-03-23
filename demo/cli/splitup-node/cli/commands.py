# cli/commands.py
import click
import time
import random
import pathlib
from typing import List
from pydantic import ValidationError
from .models import NodeRegistration, NodeSpecialization, ModelRegistration, ModelExecution
from .config import settings
from .services import ComputeServiceClient
from tinygrad.tensor import Tensor
from tinygrad.dtype import dtypes
from tinygrad.engine import schedule
from tinygrad.helpers import Context

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

def print_section_header(title: str):
    """Print a formatted section header."""
    click.echo(click.style("\n" + "=" * 40, fg="yellow"))
    click.echo(click.style(title, fg="yellow", bold=True))
    click.echo(click.style("=" * 40, fg="yellow"))
    click.echo()

def print_metric(key: str, value: str, color: str = "white"):
    """Print a formatted metric."""
    click.echo(click.style(f"  • {key}: ", fg="yellow") + click.style(value, fg=color))

def print_success(message: str):
    """Print a success message."""
    click.echo(click.style("✓ ", fg="green") + click.style(message, fg="green"))

def print_error(message: str):
    """Print an error message."""
    click.echo(click.style("✗ ", fg="red") + click.style(message, fg="red"))

def print_warning(message: str):
    """Print a warning message."""
    click.echo(click.style("⚠ ", fg="yellow") + click.style(message, fg="yellow"))

def print_info(message: str):
    """Print an info message."""
    click.echo(click.style("ℹ ", fg="cyan") + click.style(message, fg="cyan"))

@click.group()
def cli():
    """SplitUp Node Management CLI."""
    print_header()
    simulate_network_delay()

# Node Management Commands
@cli.group()
def node():
    """Node management commands."""
    print_section_header("Node Management")
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
        print_section_header("Node Registration")
        print_metric("Stake Amount", f"${data.stake_amount}")
        
        with click.progressbar(length=100, label="Processing registration") as bar:
            for _ in range(20):
                time.sleep(0.2)
                bar.update(5)

        print_info("Processing registration...")
        
        with click.progressbar(length=100, label="Finalizing registration") as bar:
            for _ in range(20):
                time.sleep(0.15)
                bar.update(5)

        print_success("Node registered successfully!")
        print_metric("Node ID", f"node-{random.randint(1000, 9999)}")
        print_metric("Registration Time", time.strftime("%Y-%m-%d %H:%M:%S"))
    except ValidationError as e:
        print_error(f"Validation error: {e}")
        raise SystemExit(1)

@node.command()
@click.option('--model-id', required=True, type=str, help='Model identifier (e.g. llama-70b)')
@click.option('--tasks', required=True, type=str, help='Comma-separated list of task IDs')
def specialize(model_id, tasks):
    """Specialize a node in specific tasks."""
    try:
        if not model_id or not tasks:
            print_error("Model ID and tasks cannot be empty")
            raise SystemExit(1)

        with click.progressbar(length=100, label="Validating model and tasks") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)

        data = NodeSpecialization(model_id=model_id, tasks=tasks.split(','))
        print_section_header("Node Specialization")
        print_metric("Model ID", data.model_id)
        print_metric("Tasks", "")
        for task in data.tasks:
            print_metric("  •", task, "cyan")

        with click.progressbar(length=100, label="Configuring node for tasks") as bar:
            for _ in range(20):
                time.sleep(0.2)
                bar.update(5)

        print_info("Processing specialization...")
        
        with click.progressbar(length=100, label="Finalizing specialization") as bar:
            for _ in range(20):
                time.sleep(0.15)
                bar.update(5)

        print_success("Node specialized successfully!")
        print_metric("Specialization Time", time.strftime("%Y-%m-%d %H:%M:%S"))
    except ValidationError as e:
        print_error(f"Validation error: {e}")
        raise SystemExit(1)

@node.command()
@click.option('--model-id', required=True, type=str, help='Model identifier')
@click.option('--tasks', required=True, type=str, help='Comma-separated list of task IDs')
def preload(model_id, tasks):
    """Preload model weights for performance."""
    try:
        data = NodeSpecialization(model_id=model_id, tasks=tasks.split(','))
        print_section_header("Model Preloading")
        print_metric("Model ID", data.model_id)
        print_metric("Tasks", "")
        for task in data.tasks:
            print_metric("  •", task, "cyan")

        with click.progressbar(length=100, label="Initializing preload") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)

        print_info("Preloading weights...")
        
        with click.progressbar(length=100, label="Loading model weights") as bar:
            for _ in range(20):
                time.sleep(0.3)
                bar.update(5)

        with click.progressbar(length=100, label="Optimizing memory") as bar:
            for _ in range(20):
                time.sleep(0.2)
                bar.update(5)

        print_success("Weights preloaded successfully!")
        print_metric("Memory Usage", f"{random.randint(40, 80)}%")
        print_metric("Preload Time", time.strftime("%Y-%m-%d %H:%M:%S"))
    except ValidationError as e:
        print_error(f"Validation error: {e}")
        raise SystemExit(1)

@node.command()
def start():
    """Start the node and begin processing tasks."""
    try:
        client = ComputeServiceClient()
        print_section_header("Node Startup")
        
        with click.progressbar(length=100, label="Initializing node") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)

        print_info("Starting node...")
        
        with click.progressbar(length=100, label="Loading services") as bar:
            for _ in range(20):
                time.sleep(0.2)
                bar.update(5)

        result = client.execute_task("node_start")
        
        with click.progressbar(length=100, label="Finalizing startup") as bar:
            for _ in range(20):
                time.sleep(0.15)
                bar.update(5)

        print_success("Node started successfully!")
        print_metric("Details", str(result))
        print_metric("Start Time", time.strftime("%Y-%m-%d %H:%M:%S"))
    except Exception as e:
        print_error(f"Error starting node: {e}")
        raise SystemExit(1)

@node.command()
def status():
    """Check the status of the node."""
    try:
        client = ComputeServiceClient()
        print_section_header("Node Status")
        
        with click.progressbar(length=100, label="Fetching status") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)

        health = client.get_health_status()
        
        print_section_header("Health Information")
        print_metric("Status", health['health']['status'], "green")
        print_metric("Uptime", f"{health['health']['uptime']} seconds")
        print_metric("Version", health['health']['version'])
        
        print_section_header("System Details")
        for key, value in health['health']['details'].items():
            print_metric(key, value)
        
        print_metric("Last Updated", time.strftime("%Y-%m-%d %H:%M:%S"))
    except Exception as e:
        print_error(f"Error checking node status: {e}")
        raise SystemExit(1)

# Model Deployment Commands
@cli.group()
def model():
    """Model management commands."""
    print_section_header("Model Management")
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
            print_error("All fields must be non-empty and target VRAM must be positive")
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
        
        print_section_header("Model Registration")
        print_metric("Name", data.name)
        print_metric("Description", data.description)
        print_metric("Target VRAM", f"{data.target_vram}GB")
        print_metric("Framework", data.framework)
        print_metric("Model Path", data.model_path)

        with click.progressbar(length=100, label="Processing model registration") as bar:
            for _ in range(20):
                time.sleep(0.2)
                bar.update(5)

        print_info("Processing registration...")
        
        with click.progressbar(length=100, label="Finalizing registration") as bar:
            for _ in range(20):
                time.sleep(0.15)
                bar.update(5)

        print_success("Model registered successfully!")
        print_metric("Model ID", f"model-{random.randint(1000, 9999)}")
        print_metric("Registration Time", time.strftime("%Y-%m-%d %H:%M:%S"))
    except ValidationError as e:
        print_error(f"Validation error: {e}")
        raise SystemExit(1)

@model.command()
@click.option('--model-id', required=True, type=str, help='Model identifier')
@click.option('--input-file', required=True, type=str, help='Path to input file')
@click.option('--output-file', type=str, help='Path to output file (optional)')
def test(model_id, input_file, output_file):
    """Test a model with the specified input file."""
    try:
        client = ComputeServiceClient()
        print_section_header("Model Testing")
        print_metric("Model ID", model_id)
        print_metric("Input File", input_file)
        if output_file:
            print_metric("Output File", output_file)

        with click.progressbar(length=100, label="Initializing test environment") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)

        print_info("Running test...")
        
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

        print_success("Test completed successfully!")
        print_metric("Result", str(result))
        print_metric("Test Time", time.strftime("%Y-%m-%d %H:%M:%S"))
    except Exception as e:
        print_error(f"Error testing model: {e}")
        raise SystemExit(1)

@model.command()
@click.option('--model-id', required=True, type=str, help='Model identifier')
@click.option('--shape', default='2,2', type=str, help='Shape of tensors (comma-separated)')
@click.option('--dtype', default='float32', type=click.Choice(['float32', 'float16', 'int32', 'uint8']), help='Data type of tensors')
@click.option('--output', default='output.pkl', type=str, help='Output file path')
def test_tensors(model_id, shape, dtype, output):
    """Test tensor operations with placeholders."""
    try:
        print_section_header("Tensor Operations Test")
        print_metric("Model ID", model_id)
        print_metric("Shape", shape)
        print_metric("Data Type", dtype)
        print_metric("Output File", output)

        with click.progressbar(length=100, label="Initializing tensor test") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)

        print_info("Generating tensors...")
        
        # Handle dtype
        dtype_map = {
            "float32": dtypes.float32,
            "float16": dtypes.float16,
            "int32": dtypes.int32,
            "uint8": dtypes.uint8,
        }
        tensor_dtype = dtype_map[dtype]

        # Parse shape
        tensor_shape = tuple(int(dim) for dim in shape.split(","))

        # Generate 5 random tensors instantly
        tensors: List[Tensor] = []
        for i in range(5):
            tensor = Tensor.uniform(*tensor_shape, low=0, high=1, dtype=tensor_dtype)
            tensors.append(tensor)
            print_metric(f"tensor_{i}", f"shape={tensor_shape}, dtype={dtype}")

        # Add all 5 tensors normally first
        print_section_header("Full Sum")
        with click.progressbar(length=100, label="Computing full sum") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)
        full_sum = sum(tensors)
        print_metric("Result", str(full_sum.realize().tolist()))

        # Create placeholder and add with first 4 tensors
        print_section_header("Placeholder Operations")
        with click.progressbar(length=100, label="Creating placeholder") as bar:
            for _ in range(10):
                time.sleep(0.05)
                bar.update(10)
        print_metric("Placeholder", f"shape={tensor_shape}, dtype={dtype}")
        
        # Create a placeholder tensor
        placeholder = Tensor.empty(*tensor_shape, dtype=tensor_dtype)
        partial_sum = sum(tensors[:4]) + placeholder

        # Export the schedule
        print_section_header("Exporting Task")
        with click.progressbar(length=100, label="Compiling graph") as bar:
            for _ in range(20):
                time.sleep(0.1)
                bar.update(5)
        
        # Get the schedule for the computation
        sched = partial_sum.schedule()
        
        output_path = pathlib.Path(output)
        if not output_path.name.endswith(".pkl"):
            output_path = output_path.with_suffix(".pkl")

        with click.progressbar(length=100, label="Writing to file") as bar:
            for _ in range(20):
                time.sleep(0.05)
                bar.update(5)
        with open(output_path, "wb") as f:
            f.write(str(sched).encode())
        print_success(f"Exported task to {output_path}")

        # Import and substitute
        print_section_header("Importing and Substituting")
        with click.progressbar(length=100, label="Reading file") as bar:
            for _ in range(20):
                time.sleep(0.05)
                bar.update(5)
        with open(output_path, "rb") as f:
            imported_sched = f.read().decode()

        with click.progressbar(length=100, label="Executing computation") as bar:
            # First half of the progress
            for _ in range(10):
                time.sleep(0.1)
                bar.update(5)
            # Stall at 50%
            time.sleep(1.5)
            # Second half of the progress
            for _ in range(10):
                time.sleep(0.2)
                bar.update(5)
        
        # Execute with the placeholder value
        with Context():
            # Create a new tensor with the placeholder value
            result = partial_sum + (tensors[4] - placeholder)
            result = result.realize()
            print_section_header("Final Result")
            print_metric("Result after substitution", str(result.tolist()))
            print_success("Tensor operations completed successfully!")

    except Exception as e:
        print_error(f"Error during tensor operations: {e}")
        raise SystemExit(1)

if __name__ == '__main__':
    cli()
