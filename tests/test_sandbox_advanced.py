import sys
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@dataclass
class MockSandboxEnv:
    id: str
    provider: str
    status: str


# Mock dependencies
mock_docker = MagicMock()
sys.modules["docker"] = mock_docker
mock_modal = MagicMock()
sys.modules["modal"] = mock_modal

from ai_dev_os.sandbox import SandboxManager, SandboxProvider


@pytest.fixture
def sandbox_manager():
    return SandboxManager()


@pytest.mark.asyncio
async def test_create_sandbox_docker(sandbox_manager):
    with patch("ai_dev_os.sandbox.SandboxFactory.create") as mock_create:
        mock_sb = MagicMock()
        mock_sb.id = "docker-123"
        mock_sb.provider = SandboxProvider.DOCKER
        mock_create.return_value = mock_sb

        env = await sandbox_manager.create_sandbox(
            provider=SandboxProvider.DOCKER, image="python:3.12"
        )

        assert env.id == "docker-123"


@pytest.mark.asyncio
async def test_execute_command_mock(sandbox_manager):
    env = MockSandboxEnv(id="123", provider="docker", status="running")
    # This hits the fallback in SandboxManager.execute_command
    result = await sandbox_manager.execute_command(env, "echo hello")
    assert result["exit_code"] == 0
    assert "echo hello" in result["stdout"]


@pytest.mark.asyncio
async def test_execute_command_real(sandbox_manager):
    mock_sb = MagicMock()
    # Define execute as an AsyncMock to support await
    mock_sb.execute = AsyncMock(return_value=(0, "success", ""))

    result = await sandbox_manager.execute_command(mock_sb, "ls")
    assert result["stdout"] == "success"


@pytest.mark.asyncio
async def test_terminate_sandbox(sandbox_manager):
    mock_sb = MagicMock()
    mock_sb.terminate = AsyncMock(return_value=True)

    success = await sandbox_manager.terminate_sandbox(mock_sb)
    assert success is True
