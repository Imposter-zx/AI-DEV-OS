from unittest.mock import MagicMock, patch

import pytest

from ai_dev_os.integrations.github import GitHubIntegration


@pytest.fixture
def github():
    with patch("ai_dev_os.integrations.github.Github"):
        return GitHubIntegration(token="fake-token")


@pytest.mark.asyncio
async def test_github_create_branch_mock(github):
    with patch.object(github.client, "get_repo") as mock_get_repo:
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo

        result = await github.create_branch("owner/repo", "new-feature")
        assert result["status"] == "success"
        mock_repo.get_branch.assert_called_once()
        mock_repo.create_git_ref.assert_called_once()


@pytest.mark.asyncio
async def test_github_create_pr_mock(github):
    with patch.object(github.client, "get_repo") as mock_get_repo:
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        mock_pr = MagicMock(number=123, html_url="http://pr")
        mock_repo.create_pull.return_value = mock_pr

        result = await github.create_pr("owner/repo", "head", "title", "desc")
        assert result["number"] == 123
        assert result["status"] == "created"


@pytest.mark.asyncio
async def test_github_add_comment_mock(github):
    with patch.object(github.client, "get_repo") as mock_get_repo:
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        mock_issue = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        result = await github.add_comment("owner/repo", 123, "nice PR")
        assert result["status"] == "success"
        mock_issue.create_comment.assert_called_once_with("nice PR")


def test_github_metrics_logic(github):
    github.branches_created = 1
    github.prs_created = 1
    github.requests_failed = 1

    metrics = github.get_metrics()
    assert metrics["success_rate"] == (2 / 3) * 100.0

    github.reset_metrics()
    assert github.branches_created == 0
