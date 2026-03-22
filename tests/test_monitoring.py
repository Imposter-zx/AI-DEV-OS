import pytest

from ai_dev_os.utils.monitoring import COST_ESTIMATE, TOKEN_USAGE, MetricsManager


@pytest.fixture
def metrics_manager():
    return MetricsManager()


def test_workflow_metrics(metrics_manager):
    metrics_manager.start_workflow("wf-1")
    metrics_manager.end_workflow("wf-1", status="success")
    # Histogram observation is harder to check directly without registry access,
    # but we can ensure no errors and logic flows.


def test_record_token_usage(metrics_manager):
    # Get current value
    initial_tokens = TOKEN_USAGE.labels(model="claude-3.5-sonnet")._value.get()

    metrics_manager.record_token_usage("claude-3.5-sonnet", 1000)

    final_tokens = TOKEN_USAGE.labels(model="claude-3.5-sonnet")._value.get()
    assert final_tokens == initial_tokens + 1000


def test_cost_estimation(metrics_manager):
    initial_cost = COST_ESTIMATE.labels(model="claude-3.5-sonnet")._value.get()

    # 1M tokens = $10
    metrics_manager.record_token_usage("claude-3.5-sonnet", 1000000)

    final_cost = COST_ESTIMATE.labels(model="claude-3.5-sonnet")._value.get()
    assert final_cost == initial_cost + 10.0


def test_update_active_agents(metrics_manager):
    metrics_manager.update_active_agents(5)
    # Gauge value check
    from ai_dev_os.utils.monitoring import ACTIVE_AGENTS

    assert ACTIVE_AGENTS._value.get() == 5
