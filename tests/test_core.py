import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from unittest.mock import MagicMock, patch

# Mock Python 3.9+ dependencies that are unavailable
sys.modules['langgraph'] = MagicMock()
sys.modules['langgraph.graph'] = MagicMock()
sys.modules['anthropic'] = MagicMock()

from ai_dev_os.core import AIDevOSOrchestrator, WorkflowState, WorkflowPhase, AgentConfig, SandboxProvider

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
