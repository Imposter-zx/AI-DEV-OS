from unittest.mock import patch

import pytest

from ai_dev_os.integrations.slack import SlackIntegration


@pytest.fixture
def slack_integration():
    with patch("slack_sdk.WebClient") as mock_client:
        integration = SlackIntegration(token="xoxb-fake")
        integration.mock_client = mock_client.return_value
        return integration


@pytest.mark.asyncio
async def test_send_threaded_message_success(slack_integration):
    slack_integration.mock_client.chat_postMessage.return_value = {"ok": True, "ts": "123.456"}

    result = await slack_integration.send_message(
        channel="C123", text="Hello world", thread_ts="111.222"
    )

    assert result["status"] == "success"
    assert result["ts"] == "123.456"
    slack_integration.mock_client.chat_postMessage.assert_called_once_with(
        channel="C123", text="Hello world", thread_ts="111.222"
    )


@pytest.mark.asyncio
async def test_send_interactive_blocks_success(slack_integration):
    slack_integration.mock_client.chat_postMessage.return_value = {"ok": True, "ts": "789.0"}
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Approve changes?"}}]

    result = await slack_integration.send_message(channel="C123", blocks=blocks)

    assert result["status"] == "success"
    slack_integration.mock_client.chat_postMessage.assert_called_once_with(
        channel="C123", blocks=blocks
    )


@pytest.mark.asyncio
async def test_handle_interaction_payload_parsing(slack_integration):
    payload = {
        "type": "block_actions",
        "actions": [{"action_id": "approve_pr", "value": "123"}],
        "channel": {"id": "C123"},
        "message": {"ts": "456.789"},
    }

    result = await slack_integration.handle_interaction(payload)

    assert result["action"] == "approve_pr"
    assert result["value"] == "123"
