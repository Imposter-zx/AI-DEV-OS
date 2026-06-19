from unittest.mock import patch

import pytest

from ai_dev_os.integrations.github import GitHubIntegration
from ai_dev_os.sandbox import SandboxConfig, SandboxFactory, SandboxManager


@pytest.mark.asyncio
async def test_sandbox_factory_error():
    config = SandboxConfig(provider="unknown", name="test")
    with pytest.raises(ValueError, match="Unknown provider"):
        await SandboxFactory.create(config)


@pytest.mark.asyncio
async def test_sandbox_manager_terminate_fallback():
    manager = SandboxManager()

    # Create an object definitely without 'terminate'
    class NoTerminate:
        pass

    res = await manager.terminate_sandbox(NoTerminate())
    assert res is True


@pytest.mark.asyncio
async def test_github_integration_errors():
    # Test missing token
    with pytest.raises(ValueError, match="GitHub token is missing"):
        GitHubIntegration(token="")

    # Test GithubException coverage
    with patch("ai_dev_os.integrations.github.HAS_GITHUB", True), \
         patch("ai_dev_os.integrations.github.Github") as mock_gh_class:

        mock_client = mock_gh_class.return_value
        github = GitHubIntegration(token="fake")

        from github import GithubException

        mock_client.get_repo.side_effect = GithubException(
            status=404, data={"message": "Not Found"}
        )

        res = await github.create_pr("repo", "branch", "title", "desc")
        assert "error" in res["status"]
        assert github.requests_failed == 1

        # Test add_comment error
        mock_client.get_repo.side_effect = GithubException(
            status=401, data={"message": "Unauthorized"}
        )
        res = await github.add_comment("repo", 1, "body")
        assert res["status"] == "error"

        # Unexpected error in create_branch
        mock_client.get_repo.side_effect = Exception("Crash")
        res = await github.create_branch("repo", "branch")
        assert res["status"] == "error"

        # Unexpected error in create_pr
        mock_client.get_repo.side_effect = Exception("PR Crash")
        res = await github.create_pr("repo", "br", "t", "d")
        assert "error" in res["status"]

        # Unexpected error in add_comment
        mock_client.get_repo.side_effect = Exception("Comment Crash")
        res = await github.add_comment("repo", 1, "b")
        assert res["status"] == "error"


def test_github_metrics_zero_division():
    github = GitHubIntegration(token="fake")
    github.reset_metrics()
    metrics = github.get_metrics()
    assert metrics["success_rate"] == 0.0
