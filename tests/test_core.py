import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from ai_dev_os.core import (
    AgentConfig,
    AIDevOSOrchestrator,
    SandboxProvider,
    WorkflowPhase,
    WorkflowState,
)


@pytest.fixture
def mock_anthropic():
    with patch("ai_dev_os.core.Anthropic") as mock:
        yield mock


@pytest.mark.asyncio
async def test_orchestrator_initialization(mock_anthropic):
    orchestrator = AIDevOSOrchestrator(sandbox_provider=SandboxProvider.DOCKER)
    assert orchestrator.sandbox_provider == SandboxProvider.DOCKER
    assert "brainstorming" in orchestrator.skills


@pytest.mark.asyncio
async def test_workflow_state_logging():
    state = WorkflowState(id="test-1", phase=WorkflowPhase.BRAINSTORMING, user_request="test")
    state.add_log("Testing log")
    assert len(state.logs) == 1
    assert "Testing log" in state.logs[0]


@pytest.mark.asyncio
async def test_agent_config_defaults():
    config = AgentConfig(name="test-agent", role="code", sandbox_provider=SandboxProvider.MODAL)
    assert "read_file" in config.tools
    assert "write_file" in config.tools
    assert config.max_tokens == 50000
