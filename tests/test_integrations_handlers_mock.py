from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_dev_os.integrations.github import GitHubIntegration
from ai_dev_os.integrations.linear import LinearIntegration
from ai_dev_os.integrations.slack import SlackIntegration


@pytest.mark.asyncio
async def test_slack_handlers_mock():
    slack = SlackIntegration(token="fake")

    # handle_message
    res = await slack.handle_message({"text": "Hello @openswe"})
    assert res["status"] == "accepted"

    res = await slack.handle_message({"text": "Just chat"})
    assert res["status"] == "ignored"

    # handle_interaction
    res = await slack.handle_interaction(
        {"type": "block_actions", "actions": [{"action_id": "click", "value": "val"}]}
    )
    assert res["action"] == "click"

    res = await slack.handle_interaction({"type": "other"})
    assert res["status"] == "unknown_interaction"


@pytest.mark.asyncio
async def test_linear_handlers_mock():
    linear = LinearIntegration(api_key="fake")

    # handle_issue
    res = await linear.handle_issue({"data": {"title": "Fix bug @openswe", "id": "123"}})
    assert res["status"] == "processing"

    res = await linear.handle_issue({"data": {"title": "Just a bug"}})
    assert res["status"] == "ignored"

    # update_issue_status
    with patch("httpx.AsyncClient") as mock_httpx:
        mock_client = mock_httpx.return_value.__aenter__.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"issueUpdate": {"success": True}}}
        mock_client.post = AsyncMock(return_value=mock_response)

        result = await linear.update_issue_status("ISS-1", "Done")
        assert result["success"] is True


@pytest.mark.asyncio
async def test_github_webhook_mock():
    github = GitHubIntegration(token="fake")
    res = await github.handle_webhook_comment({"comment": {"body": "Check this @openswe"}})
    assert res["status"] == "queued"

    res = await github.handle_webhook_comment({"comment": {"body": "No tag"}})
    assert res["status"] == "ignored"
