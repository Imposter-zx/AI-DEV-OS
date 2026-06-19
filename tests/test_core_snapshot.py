from pathlib import Path
from unittest.mock import patch

import pytest

from ai_dev_os.core import AIDevOSOrchestrator


@pytest.fixture
def orchestrator(tmp_path):
    # Completely isolate the home directory for the entire core module during testing
    with patch("ai_dev_os.core.AnthropicLLM") as mock_llm_class, \
         patch("ai_dev_os.core.SnapshotManager") as mock_sm_class, \
         patch("ai_dev_os.core.Path.home", return_value=tmp_path):

        mock_llm = mock_llm_class.return_value
        mock_sm = mock_sm_class.return_value
        mock_sm.save_snapshot.return_value = Path("dummy")

        orch = AIDevOSOrchestrator()
        orch.snapshot_manager = mock_sm
        orch.mock_llm = mock_llm
        # Also fix the skills
        for skill in orch.skills.values():
            skill.llm = mock_llm
        return orch


@pytest.mark.asyncio
async def test_run_generates_snapshots(orchestrator):
    orchestrator.mock_llm.generate.return_value = ("mock result phase 1", 10, 10)

    with patch("builtins.input", return_value="yes"):
        await orchestrator.run("test snapshot request")

    assert orchestrator.snapshot_manager.save_snapshot.call_count >= 5

    calls = orchestrator.snapshot_manager.save_snapshot.call_args_list
    phases = [call[0][1] for call in calls]
    assert "brainstorming" in phases
    assert "planning" in phases


@pytest.mark.asyncio
async def test_retry_on_api_failure(orchestrator):
    # Explicitly patch out the cache checking logic to ensure we always hit the API
    with patch("ai_dev_os.core.Path.exists", return_value=False):
        orchestrator.mock_llm.generate.side_effect = [
            Exception("transient error"),
            ("success result", 10, 10),
        ]

        with patch("builtins.input", return_value="no"):
            state = await orchestrator.run("unique request for retry test")

        assert state.design_doc == "success result"
        assert orchestrator.mock_llm.generate.call_count == 2
