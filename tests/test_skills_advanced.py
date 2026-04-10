from unittest.mock import AsyncMock, patch

import pytest

from ai_dev_os.core import AIDevOSOrchestrator, WorkflowPhase, WorkflowState


@pytest.fixture
def orchestrator():
    with (
        patch("anthropic.Anthropic"),
        patch("ai_dev_os.core.SnapshotManager"),
        patch("ai_dev_os.core.AIDevOSOrchestrator._load_agents_rules", return_value={}),
    ):
        return AIDevOSOrchestrator()


@pytest.mark.asyncio
async def test_new_skills_initialized(orchestrator):
    assert "research" in orchestrator.skills
    assert "security-audit" in orchestrator.skills
    assert "performance-optimization" in orchestrator.skills

    assert orchestrator.skills["research"].name == "research"
    assert orchestrator.skills["security-audit"].trigger == "Discovery" or "Safety Check"


@pytest.mark.asyncio
async def test_research_skill_execution(orchestrator):
    # Mock the execute method of the research skill
    state = WorkflowState(id="1", phase=WorkflowPhase.BRAINSTORMING, user_request="fix bugs")

    with patch.object(
        orchestrator.skills["research"], "execute", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = "Research findings: found 3 bugs."
        result = await orchestrator.skills["research"].execute(state)
        assert "3 bugs" in result
        mock_exec.assert_called_once_with(state)


@pytest.mark.asyncio
async def test_security_audit_skill_execution(orchestrator):
    state = WorkflowState(id="2", phase=WorkflowPhase.BRAINSTORMING, user_request="audit code")

    with patch.object(
        orchestrator.skills["security-audit"], "execute", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = "Security findings: 0 vulnerabilities."
        result = await orchestrator.skills["security-audit"].execute(state)
        assert "0 vulnerabilities" in result
        mock_exec.assert_called_once_with(state)
