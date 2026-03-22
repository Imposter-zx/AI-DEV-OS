import os

import pytest


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Set dummy environment variables for tests."""
    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-dummy-key-for-testing"
