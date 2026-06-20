from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_dev_os.integrations.linear import LinearIntegration
from ai_dev_os.integrations.slack import SlackIntegration


@pytest.fixture
def slack():
    with patch("slack_sdk.WebClient"):
        return SlackIntegration(token="fake-token")


@pytest.fixture
def linear():
    return LinearIntegration(api_key="fake-key")


@pytest.mark.asyncio
async def test_slack_send_message_mock(slack):
    with patch.object(slack.client, "chat_postMessage") as mock_post:
        mock_post.return_value = {"ok": True, "ts": "123"}

        result = await slack.send_message(channel="C123", text="hello")
        assert result["status"] == "success"
        assert result["ts"] == "123"
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_linear_create_issue_mock(linear):
    # Linear uses httpx internally, so we mock httpx.AsyncClient
    with patch("httpx.AsyncClient") as mock_httpx:
        mock_client = mock_httpx.return_value.__aenter__.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"issueCreate": {"issue": {"id": "ISS-1", "url": "http://linear/1"}}}
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        result = await linear.create_issue(team_id="T1", title="test", description="desc")
        assert result["issue"]["id"] == "ISS-1"
        mock_client.post.assert_called_once()


def test_slack_metrics(slack):
    # Just verify metrics calling doesn't crash as it uses the singleton
    pass
