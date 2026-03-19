import pytest
from ai_dev_os.sandbox import SandboxConfig, ModalSandbox, SandboxStatus

@pytest.mark.asyncio
async def test_sandbox_config():
    config = SandboxConfig(provider="modal", name="test-sandbox", gpu=True)
    assert config.provider == "modal"
    assert config.gpu is True

@pytest.mark.asyncio
async def test_modal_sandbox_mock():
    config = SandboxConfig(provider="modal", name="test-sandbox")
    # Mocking modal import if needed, but the class handles it
    sandbox = ModalSandbox(config)
    assert sandbox.status == SandboxStatus.INITIALIZING
    
    # Since initialize() requires 'modal' package, we might skip or mock it
    # For this test, we just check the status change in execute
    exit_code, stdout, stderr = await sandbox.execute("ls")
    assert exit_code == 0
    assert "ls completed" in stdout
