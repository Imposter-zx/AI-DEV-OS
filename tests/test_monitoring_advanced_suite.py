from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_dev_os.monitoring_metrics import HAS_PROMETHEUS, MonitoredOrchestrator, start_metrics_server


@pytest.fixture(autouse=True)
def mock_prometheus():
    if not HAS_PROMETHEUS:
        pytest.skip("prometheus_client not installed")


@pytest.mark.asyncio
async def test_monitored_orchestrator_success():
    mock_orch = AsyncMock()
    mock_state = MagicMock()
    mock_state.context_usage = 50.0
    mock_state.subagent_configs = [MagicMock(name="agent1", role="dev")]
    mock_orch.run.return_value = mock_state

    monitored = MonitoredOrchestrator(mock_orch)
    state = await monitored.run("test request")

    assert state == mock_state
    mock_orch.run.assert_called_once_with("test request")


@pytest.mark.asyncio
async def test_monitored_orchestrator_error():
    mock_orch = AsyncMock()
    mock_orch.run.side_effect = Exception("Workflow failed")

    monitored = MonitoredOrchestrator(mock_orch)
    with pytest.raises(Exception, match="Workflow failed"):
        await monitored.run("test request")


def test_start_metrics_server():
    with patch("ai_dev_os.monitoring_metrics.start_http_server") as mock_server:
        start_metrics_server(port=9999)
        if HAS_PROMETHEUS:
            mock_server.assert_called_once_with(9999)
