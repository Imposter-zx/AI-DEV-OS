from unittest.mock import patch

import pytest

from ai_dev_os.sandbox import DockerSandbox, ModalSandbox, SandboxConfig, SandboxStatus


@pytest.mark.asyncio
async def test_modal_import_error():
    config = SandboxConfig(provider="modal", name="test")
    # Patch sys.modules to simulate missing modal
    with patch.dict("sys.modules", {"modal": None}):
        sandbox = ModalSandbox(config)
        with pytest.raises(ImportError):
            await sandbox.initialize()
        assert sandbox.status == SandboxStatus.ERROR


@pytest.mark.asyncio
async def test_docker_import_error():
    config = SandboxConfig(provider="docker", name="test")
    with patch.dict("sys.modules", {"docker": None}):
        sandbox = DockerSandbox(config)
        with pytest.raises(ImportError):
            await sandbox.initialize()
        assert sandbox.status == SandboxStatus.ERROR
