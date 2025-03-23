import pytest
from click.testing import CliRunner
import sys
import os
from unittest.mock import patch
from pydantic import ValidationError

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

@patch('cli.commands.ComputeServiceClient')
def test_node_start_success(mock_client_class, runner, mock_task_response):
    """Test successful node start command."""
    mock_client = mock_client_class.return_value
    mock_client.execute_task.return_value = mock_task_response
    
    result = runner.invoke(cli, ['node', 'start'])
    assert result.exit_code == 0
    assert "Node started successfully" in result.output
    mock_client.execute_task.assert_called_once_with("node_start")

@patch('cli.commands.ComputeServiceClient')
def test_node_start_failure(mock_client_class, runner):
    """Test node start command with service error."""
    mock_client = mock_client_class.return_value
    mock_client.execute_task.side_effect = Exception("Service error")
    
    result = runner.invoke(cli, ['node', 'start'])
    assert result.exit_code == 1
    assert "Error starting node" in result.output

@patch('cli.commands.ComputeServiceClient')
def test_node_status_success(mock_client_class, runner, mock_health_response):
    """Test successful node status command."""
    mock_client = mock_client_class.return_value
    mock_client.get_health_status.return_value = mock_health_response
    
    result = runner.invoke(cli, ['node', 'status'])
    assert result.exit_code == 0
    assert "Node status: healthy" in result.output
    assert "Uptime: 3600 seconds" in result.output
    assert "Version: 1.0.0" in result.output
    assert "cpu_usage: 45%" in result.output
    assert "memory_usage: 60%" in result.output
    assert "gpu_usage: 30%" in result.output
    mock_client.get_health_status.assert_called_once()

@patch('cli.commands.ComputeServiceClient')
def test_node_status_failure(mock_client_class, runner):
    """Test node status command with service error."""
    mock_client = mock_client_class.return_value
    mock_client.get_health_status.side_effect = Exception("Service error")
    
    result = runner.invoke(cli, ['node', 'status'])
    assert result.exit_code == 1
    assert "Error checking node status" in result.output

def test_model_register(runner):
    """Test model registration command."""
    result = runner.invoke(cli, [
        'model', 'register',
        '--model-path', 'llama-70b.pkl',
        '--target-vram', '12',
        '--name', 'llama-70b',
        '--description', 'Large language model',
        '--framework', 'tinygrad'
    ])
    assert result.exit_code == 0
    assert "Registering model: llama-70b" in result.output
    assert "Target VRAM: 12GB" in result.output
    assert "Framework: tinygrad" in result.output

@patch('cli.commands.ComputeServiceClient')
def test_model_test_success(mock_client_class, runner, mock_task_response):
    """Test successful model test command."""
    mock_client = mock_client_class.return_value
    mock_client.execute_task.return_value = mock_task_response
    
    result = runner.invoke(cli, [
        'model', 'test',
        '--model-id', 'llama-70b',
        '--input-file', 'input.txt',
        '--output-file', 'output.txt'
    ])
    assert result.exit_code == 0
    assert "Model test started" in result.output
    mock_client.execute_task.assert_called_once_with(
        "model_test",
        ["input.txt", "output.txt"]
    )

@patch('cli.commands.ComputeServiceClient')
def test_model_test_without_output(mock_client_class, runner, mock_task_response):
    """Test model test command without output file."""
    mock_client = mock_client_class.return_value
    mock_client.execute_task.return_value = mock_task_response
    
    result = runner.invoke(cli, [
        'model', 'test',
        '--model-id', 'llama-70b',
        '--input-file', 'input.txt'
    ])
    assert result.exit_code == 0
    assert "Model test started" in result.output
    mock_client.execute_task.assert_called_once_with(
        "model_test",
        ["input.txt"]
    )

@patch('cli.commands.ComputeServiceClient')
def test_model_test_failure(mock_client_class, runner):
    """Test model test command with service error."""
    mock_client = mock_client_class.return_value
    mock_client.execute_task.side_effect = Exception("Service error")
    
    result = runner.invoke(cli, [
        'model', 'test',
        '--model-id', 'llama-70b',
        '--input-file', 'input.txt'
    ])
    assert result.exit_code == 1
    assert "Error testing model" in result.output

def test_invalid_node_specialize(runner):
    """Test node specialization command with invalid input."""
    result = runner.invoke(cli, ['node', 'specialize', '--model-id', '', '--tasks', ''])
    assert result.exit_code == 1
    assert "Model ID and tasks cannot be empty" in result.output

def test_invalid_model_register(runner):
    """Test model registration command with invalid input."""
    result = runner.invoke(cli, [
        'model', 'register',
        '--model-path', '',
        '--target-vram', '-1',
        '--name', '',
        '--description', '',
        '--framework', ''
    ])
    assert result.exit_code == 1
    assert "All fields must be non-empty and target VRAM must be positive" in result.output 