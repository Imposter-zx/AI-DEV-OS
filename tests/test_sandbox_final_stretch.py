from unittest.mock import MagicMock, patch

import pytest

from ai_dev_os.sandbox import DockerSandbox, SandboxConfig, SandboxStatus


@pytest.mark.asyncio
async def test_docker_sandbox_execute_error():
    with patch("docker.from_env") as mock_docker:
        mock_client = mock_docker.return_value
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container

        sandbox = DockerSandbox(SandboxConfig(provider="docker", name="test"))
        await sandbox.initialize()

        # Test exception in execute
        mock_container.exec_run.side_effect = Exception("Exec failure")
        exit_code, stdout, stderr = await sandbox.execute("ls")
        assert exit_code == 1
        assert "Exec failure" in stderr
        assert sandbox.status == SandboxStatus.ERROR


@pytest.mark.asyncio
async def test_docker_sandbox_upload_error():
    with patch("docker.from_env") as mock_docker:
        mock_client = mock_docker.return_value
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container

        sandbox = DockerSandbox(SandboxConfig(provider="docker", name="test"))
        await sandbox.initialize()

        mock_container.put_archive.side_effect = Exception("Upload failure")
        success = await sandbox.upload_file("local", "remote")
        assert success is False


@pytest.mark.asyncio
async def test_docker_sandbox_download_error():
    with patch("docker.from_env") as mock_docker:
        mock_client = mock_docker.return_value
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container

        sandbox = DockerSandbox(SandboxConfig(provider="docker", name="test"))
        await sandbox.initialize()

        mock_container.get_archive.side_effect = Exception("Download failure")
        success = await sandbox.download_file("remote", "local")
        assert success is False


@pytest.mark.asyncio
async def test_docker_sandbox_terminate_error():
    with patch("docker.from_env") as mock_docker:
        mock_client = mock_docker.return_value
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container

        sandbox = DockerSandbox(SandboxConfig(provider="docker", name="test"))
        await sandbox.initialize()

        mock_container.stop.side_effect = Exception("Stop failure")
        success = await sandbox.terminate()
        assert success is False
