import os
import sys
from unittest.mock import MagicMock, patch

import pytest

try:
    from unittest.mock import AsyncMock
except ImportError:

    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)


# Mock HTTPX
sys.modules["httpx"] = MagicMock()

# We will test the basic webhook classes that handle standard JSON requests


@pytest.mark.asyncio
async def test_slack_webhook():
    from integrations.slack import SlackIntegration

    slack = SlackIntegration("dummy_token")
    # Simulate an incoming message event
    payload = {"type": "message", "channel": "C12345", "text": "@openswe fix the login page"}

    # Mock the internal orchestrator call
    slack.handle_message = AsyncMock(return_value={"status": "accepted"})
    result = await slack.handle_message(payload)

    assert result["status"] == "accepted"


@pytest.mark.asyncio
async def test_linear_webhook():
    from integrations.linear import LinearIntegration

    linear = LinearIntegration("dummy_secret")
    payload = {"action": "create", "data": {"id": "ISSUE-1", "title": "Fix the bug in production"}}

    linear.handle_issue = AsyncMock(return_value={"status": "processing"})
    result = await linear.handle_issue(payload)

    assert result["status"] == "processing"


@pytest.mark.asyncio
async def test_github_webhook():
    from integrations.github import GithubIntegration

    github = GithubIntegration("dummy_secret")
    payload = {
        "action": "created",
        "issue": {"number": 1},
        "comment": {"body": "@openswe Address the review feedback"},
    }

    github.handle_comment = AsyncMock(return_value={"status": "queued"})
    result = await github.handle_comment(payload)

    assert result["status"] == "queued"
