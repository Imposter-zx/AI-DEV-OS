from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_dev_os.sandbox import Sandbox, SandboxConfig, SandboxManager, SandboxStatus


class MockSandbox(Sandbox):
    async def initialize(self) -> str:
        self.id = "mock-id"
        self.status = SandboxStatus.READY
        return self.id

    async def execute(self, command: str, cwd: str = "/workspace"):
        return (0, f"Mock output for {command}", "")

    async def upload_file(self, local_path: str, remote_path: str):
        return True

    async def download_file(self, remote_path: str, local_path: str):
        return True

    async def terminate(self):
        self.status = SandboxStatus.TERMINATED
        return True


@pytest.mark.asyncio
async def test_sandbox_manager_lifecycle():
    manager = SandboxManager()

    # Register our mock provider
    with patch("ai_dev_os.sandbox.SandboxFactory._providers", {"mock": MockSandbox}):
        # Create
        sandbox = await manager.create_sandbox(provider="mock", name="test-sb")
        assert sandbox.id == "mock-id"
        assert sandbox.status == SandboxStatus.READY
        assert "mock-id" in manager.active_sandboxes

        # Execute
        result = await manager.execute_command(sandbox, "ls")
        assert result["exit_code"] == 0
        assert "Mock output for ls" in result["stdout"]

        # Terminate
        success = await manager.terminate_sandbox(sandbox)
        assert success is True
        assert sandbox.status == SandboxStatus.TERMINATED


@pytest.mark.asyncio
async def test_sandbox_manager_fallback():
    manager = SandboxManager()
    # Test execution on non-sandbox object (mock environment)
    mock_env = MagicMock()
    del mock_env.execute  # Ensure it doesn't have execute

    result = await manager.execute_command(mock_env, "echo hi")
    assert result["exit_code"] == 0
    assert "Executed: echo hi" in result["stdout"]


@pytest.mark.asyncio
async def test_sandbox_config_defaults():
    config = SandboxConfig(provider="docker", name="test")
    assert config.python_version == "3.10"
    assert config.env_vars == {}
    assert config.mounts == {}
