from unittest.mock import MagicMock, patch

import pytest

from ai_dev_os.integrations.linear import LinearIntegration


@pytest.fixture
def linear_integration():
    return LinearIntegration(api_key="fake-key")


@pytest.mark.asyncio
async def test_create_issue_success(linear_integration):
    # Mock the linear-python library if used, or httpx if using raw API
    with patch("ai_dev_os.integrations.linear.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"issueCreate": {"issue": {"id": "ISS-1", "url": "http://linear.app/1"}}}
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        result = await linear_integration.create_issue("team-id", "title", "body")

        assert result["issue"]["id"] == "ISS-1"
        assert result["issue"]["url"] == "http://linear.app/1"


@pytest.mark.asyncio
async def test_update_issue_status(linear_integration):
    with patch("ai_dev_os.integrations.linear.httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"issueUpdate": {"success": True}}}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        success = await linear_integration.update_issue_status("ISS-1", "Done")
        assert success["success"] is True


@pytest.mark.asyncio
async def test_handle_issue_webhook(linear_integration):
    payload = {
        "action": "create",
        "data": {"id": "ISS-1", "title": "Fix bug @openswe", "description": "Please help"},
    }

    result = await linear_integration.handle_issue(payload)

    assert result["status"] == "processing"
    assert "ISS-1" in result["message"]


@pytest.mark.asyncio
async def test_handle_issue_webhook_no_trigger(linear_integration):
    payload = {"action": "create", "data": {"id": "ISS-1", "title": "Normal issue"}}

    result = await linear_integration.handle_issue(payload)
    assert result["status"] == "ignored"
