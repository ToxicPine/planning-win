import pytest
from click.testing import CliRunner
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.commands import cli
from cli.config import settings

@pytest.fixture
def runner():
    return CliRunner()

def test_node_register(runner):
    """Test node registration command."""
    result = runner.invoke(cli, ['node', 'register'])
    assert result.exit_code == 0
    assert "Registering node with stake: $100" in result.output

def test_node_specialize(runner):
    """Test node specialization command."""
    result = runner.invoke(cli, ['node', 'specialize', '--model-id', 'llama-70b', '--tasks', 'task1,task2'])
    assert result.exit_code == 0
    assert "Specializing node for model llama-70b with tasks: ['task1', 'task2']" in result.output

def test_node_preload(runner):
    """Test model weight preloading command."""
    result = runner.invoke(cli, ['node', 'preload', '--model-id', 'llama-70b', '--tasks', 'task1,task2'])
    assert result.exit_code == 0
    assert "Preloading weights for model llama-70b on tasks: ['task1', 'task2']" in result.output

def test_node_start(runner):
    """Test node start command."""
    result = runner.invoke(cli, ['node', 'start'])
    assert result.exit_code == 0
    assert "Starting node services..." in result.output

def test_node_status(runner):
    """Test node status command."""
    result = runner.invoke(cli, ['node', 'status'])
    assert result.exit_code == 0
    assert "Fetching node status..." in result.output

def test_model_register(runner):
    """Test model registration command."""
    result = runner.invoke(cli, [
        'model', 'register',
        '--model-path', 'llama-70b.pkl',
        '--target-vram', '12',
        '--name', 'LLaMA 70B',
        '--description', 'Meta\'s 70B Parameter LLM',
        '--framework', 'tinygrad'
    ])
    assert result.exit_code == 0
    assert "Registering model: LLaMA 70B" in result.output
    assert "Target VRAM: 12GB" in result.output
    assert "Framework: tinygrad" in result.output

def test_model_test(runner):
    """Test model execution command."""
    result = runner.invoke(cli, [
        'model', 'test',
        '--model-id', 'llama-70b',
        '--input-file', 'prompt.json',
        '--output-file', 'output.json'
    ])
    assert result.exit_code == 0
    assert "Testing model execution for llama-70b" in result.output
    assert "Input file: prompt.json" in result.output
    assert "Output file: output.json" in result.output

def test_model_test_without_output(runner):
    """Test model execution command without output file."""
    result = runner.invoke(cli, [
        'model', 'test',
        '--model-id', 'llama-70b',
        '--input-file', 'prompt.json'
    ])
    assert result.exit_code == 0
    assert "Testing model execution for llama-70b" in result.output
    assert "Input file: prompt.json" in result.output
    assert "Output file: None" in result.output

def test_invalid_node_specialize(runner):
    """Test node specialization command with invalid input."""
    result = runner.invoke(cli, ['node', 'specialize'])
    assert result.exit_code != 0
    assert "Error: Missing option '--model-id'" in result.output

def test_invalid_model_register(runner):
    """Test model registration command with invalid input."""
    result = runner.invoke(cli, ['model', 'register'])
    assert result.exit_code != 0
    assert "Error: Missing option '--model-path'" in result.output 