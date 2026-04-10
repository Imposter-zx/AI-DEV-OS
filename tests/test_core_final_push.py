from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_dev_os.core import AIDevOSOrchestrator, WorkflowPhase, WorkflowState


@pytest.mark.asyncio
async def test_workflow_state_initialization():
    state = WorkflowState(id="1", phase=WorkflowPhase.PLANNING, user_request="test")
    assert state.id == "1"
    assert state.phase == WorkflowPhase.PLANNING
    assert state.context_usage == 0.0


@pytest.mark.asyncio
async def test_orchestrator_initialization_error():
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}):
        # AnthropicLLM should fail
        from ai_dev_os.core import AnthropicLLM

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY environment variable is missing"):
            AnthropicLLM()


@pytest.mark.asyncio
async def test_local_llm_import_error():
    from ai_dev_os.core import LocalLLM

    with patch.dict("sys.modules", {"llama_cpp": None}):
        with pytest.raises(RuntimeError, match="llama-cpp-python is required"):
            LocalLLM("path")


@pytest.mark.asyncio
async def test_agent_config_defaults():
    from ai_dev_os.core import AgentConfig, SandboxProvider

    config = AgentConfig(name="test", role="code", sandbox_provider=SandboxProvider.DOCKER)
    assert "read_file" in config.tools

    config2 = AgentConfig(name="test", role="training", sandbox_provider=SandboxProvider.MODAL)
    assert "unsloth_train" in config2.tools
