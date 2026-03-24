import pytest

from ai_dev_os.sandbox import ModalSandbox, SandboxConfig, SandboxStatus


@pytest.mark.asyncio
async def test_sandbox_config():
    config = SandboxConfig(provider="modal", name="test-sandbox", gpu=True)
    assert config.provider == "modal"
    assert config.gpu is True


@pytest.mark.asyncio
async def test_modal_sandbox_mock():
    config = SandboxConfig(provider="modal", name="test-sandbox")
    sandbox = ModalSandbox(config)
    assert sandbox.status == SandboxStatus.INITIALIZING

    # Without 'modal' actual initialization, the sandbox.app attribute will not exist,
    # causing an AttributeError which our broad except catches and returns (1, '', str(e))
    exit_code, stdout, stderr = await sandbox.execute("ls")
    assert exit_code == 1
    assert "object has no attribute 'app'" in stderr or "No module named 'modal'" in stderr
