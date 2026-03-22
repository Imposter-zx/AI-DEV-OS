import pytest

from ai_dev_os.utils.context import ContextManager


@pytest.fixture
def context_manager():
    return ContextManager()


def test_count_tokens(context_manager):
    text = "Hello world!"
    tokens = context_manager.count_tokens(text)
    assert tokens > 0


def test_track_usage(context_manager):
    context_manager.track_usage("wf-1", "agent-1", 500)
    context_manager.track_usage("wf-1", "agent-2", 300)

    assert context_manager.workflow_usage["wf-1"] == 800
    assert context_manager.agent_usage["agent-1"] == 500


def test_should_summarize(context_manager):
    context_manager.track_usage("wf-1", "agent-1", 900)

    # 900 / 1000 = 90%
    assert context_manager.should_summarize("wf-1", 1000, threshold=90.0) is True
    assert context_manager.should_summarize("wf-1", 2000, threshold=90.0) is False


def test_generate_summary_prompt(context_manager):
    logs = ["step 1", "step 2"]
    prompt = context_manager.generate_summary_prompt(logs)
    assert "step 1" in prompt
    assert "90%+" in prompt
