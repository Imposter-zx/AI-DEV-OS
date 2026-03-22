from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_dev_os.core import AIDevOSOrchestrator, WorkflowPhase


@pytest.fixture
def orchestrator(tmp_path):
    # Completely isolate the home directory for the entire core module during testing
    with (
        patch("ai_dev_os.core.Anthropic") as mock_anth_class,
        patch("ai_dev_os.core.SnapshotManager") as mock_sm_class,
        patch("ai_dev_os.core.Path.home", return_value=tmp_path),
    ):

        mock_anth = mock_anth_class.return_value
        mock_sm = mock_sm_class.return_value
        mock_sm.save_snapshot.return_value = Path("dummy")

        orch = AIDevOSOrchestrator()
        orch.snapshot_manager = mock_sm
        orch.mock_anth = mock_anth
        return orch


@pytest.mark.asyncio
async def test_run_generates_snapshots(orchestrator):
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text="mock result phase 1")]
    mock_resp.usage.output_tokens = 10
    orchestrator.mock_anth.messages.create.return_value = mock_resp

    with patch("builtins.input", return_value="yes"):
        state = await orchestrator.run("test snapshot request")

    assert orchestrator.snapshot_manager.save_snapshot.call_count >= 5

    calls = orchestrator.snapshot_manager.save_snapshot.call_args_list
    phases = [call[0][1] for call in calls]
    assert "brainstorming" in phases
    assert "planning" in phases


@pytest.mark.asyncio
async def test_retry_on_api_failure(orchestrator):
    # Explicitly patch out the cache checking logic to ensure we always hit the API
    with patch("ai_dev_os.core.Path.exists", return_value=False):
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="success result")]
        mock_resp.usage.output_tokens = 10

        orchestrator.mock_anth.messages.create.side_effect = [
            Exception("transient error"),
            mock_resp,
        ]

        with patch("builtins.input", return_value="no"):
            state = await orchestrator.run("unique request for retry test")

        assert state.design_doc == "success result"
        assert orchestrator.mock_anth.messages.create.call_count == 2
