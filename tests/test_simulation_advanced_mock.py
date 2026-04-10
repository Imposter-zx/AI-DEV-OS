import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_dev_os.simulation import NewtonSimulation, SimulationConfig, SimulationResult


@pytest.mark.asyncio
async def test_simulation_fallback_to_mock_when_no_newton():
    # Ensure HAS_NEWTON is False for this test
    with patch("ai_dev_os.simulation.HAS_NEWTON", False):
        config = SimulationConfig(episodes=5, success_threshold=0.8)
        sim = NewtonSimulation(config)

        # This shouldn't raise RuntimeError anymore, should use mock
        result = await sim.run()

        assert isinstance(result, SimulationResult)
        assert result.total_episodes == 5
        assert result.total_time_seconds > 0
        assert 0 <= result.success_rate <= 1.0


@pytest.mark.asyncio
async def test_simulation_reports_json_metrics():
    with patch("ai_dev_os.simulation.HAS_NEWTON", False):
        config = SimulationConfig(episodes=2)
        sim = NewtonSimulation(config)
        result = await sim.run()

        # Verify we can serialize result to JSON as per project requirements
        metrics_json = json.dumps(result.__dict__)
        metrics_dict = json.loads(metrics_json)

        assert "success_rate" in metrics_dict
        assert "total_episodes" in metrics_dict
        assert metrics_dict["total_episodes"] == 2


@pytest.mark.asyncio
async def test_simulation_success_condition():
    with patch("ai_dev_os.simulation.HAS_NEWTON", False):
        # Setup config where success is almost guaranteed if mock is favorable
        # Or mock the _run_episode internally
        config = SimulationConfig(episodes=1, success_threshold=0.5)
        sim = NewtonSimulation(config)

        with patch.object(sim, "_run_episode", AsyncMock(return_value=0.9)):
            result = await sim.run()
            assert result.success_rate == 1.0
            assert result.passed is True
