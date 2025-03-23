import pytest
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.config import settings

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Store original environment variables
    original_env = {
        'SPLITUP_NODE_STAKE_AMOUNT': os.environ.get('SPLITUP_NODE_STAKE_AMOUNT'),
        'SPLITUP_NODE_SPECIALIZATION': os.environ.get('SPLITUP_NODE_SPECIALIZATION'),
        'SPLITUP_CLIENT_S3_API_KEY': os.environ.get('SPLITUP_CLIENT_S3_API_KEY'),
        'SPLITUP_CLIENT_SOLANA_PRIVATE_KEY': os.environ.get('SPLITUP_CLIENT_SOLANA_PRIVATE_KEY'),
        'SPLITUP_CLIENT_TARGET_VRAM': os.environ.get('SPLITUP_CLIENT_TARGET_VRAM'),
        'SPLITUP_CLIENT_MODEL_FRAMEWORK': os.environ.get('SPLITUP_CLIENT_MODEL_FRAMEWORK')
    }
    
    # Set test environment variables
    os.environ['SPLITUP_NODE_STAKE_AMOUNT'] = '100'
    os.environ['SPLITUP_NODE_SPECIALIZATION'] = 'test'
    os.environ['SPLITUP_CLIENT_S3_API_KEY'] = 'test_key'
    os.environ['SPLITUP_CLIENT_SOLANA_PRIVATE_KEY'] = 'test_private_key'
    os.environ['SPLITUP_CLIENT_TARGET_VRAM'] = '12'
    os.environ['SPLITUP_CLIENT_MODEL_FRAMEWORK'] = 'tinygrad'
    
    yield
    
    # Restore original environment variables
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value 