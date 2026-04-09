from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_dev_os.integrations.github import GitHubIntegration


@pytest.fixture
def github_integration():
    with patch("ai_dev_os.integrations.github.Github") as mock_github:
        integration = GitHubIntegration(token="fake-token")
        integration.mock_client = mock_github.return_value
        return integration


@pytest.mark.asyncio
async def test_create_branch_success(github_integration):
    mock_repo = MagicMock()
    github_integration.mock_client.get_repo.return_value = mock_repo
    mock_branch = MagicMock()
    mock_repo.get_branch.return_value = mock_branch
    mock_branch.commit.sha = "123456"

    result = await github_integration.create_branch("user/repo", "new-branch")

    assert result["status"] == "success"
    mock_repo.create_git_ref.assert_called_once_with(ref="refs/heads/new-branch", sha="123456")


@pytest.mark.asyncio
async def test_create_pr_success(github_integration):
    mock_repo = MagicMock()
    github_integration.mock_client.get_repo.return_value = mock_repo
    mock_pr = MagicMock()
    mock_pr.html_url = "https://github.com/user/repo/pull/1"
    mock_pr.number = 1
    mock_repo.create_pull.return_value = mock_pr

    result = await github_integration.create_pr("user/repo", "head", "title", "body")

    assert result["status"] == "created"
    assert result["number"] == 1
    assert result["url"] == "https://github.com/user/repo/pull/1"


@pytest.mark.asyncio
async def test_add_comment_success(github_integration):
    mock_repo = MagicMock()
    github_integration.mock_client.get_repo.return_value = mock_repo
    mock_issue = MagicMock()
    mock_repo.get_issue.return_value = mock_issue

    result = await github_integration.add_comment("user/repo", 1, "test-comment")

    assert result["status"] == "success"
    mock_issue.create_comment.assert_called_once_with("test-comment")


@pytest.mark.asyncio
async def test_webhook_comment_trigger(github_integration):
    payload = {"action": "created", "comment": {"body": "Please help @openswe fix this"}}

    result = await github_integration.handle_webhook_comment(payload)

    assert result["status"] == "queued"
    assert "Feedback received" in result["message"]
