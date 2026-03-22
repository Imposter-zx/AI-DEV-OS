"""
GitHub integration for AI Dev OS.

Handles repository operations, PR creation, and branch management using PyGithub.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from github import Github, GithubException

    HAS_GITHUB = True
except ImportError:
    logger.info("PyGithub not installed. GitHub integration will be mocked.")
    HAS_GITHUB = False


class GitHubIntegration:
    """
    Handles GitHub operations for autonomous agents.
    """

    def __init__(self, token: str):
        if not token or token.strip() == "":
            raise ValueError("CRITICAL SECURITY ERROR: GitHub token is missing or empty.")
        self.token = token
        self.client = Github(token) if HAS_GITHUB else None

    async def create_branch(
        self, repo_name: str, branch_name: str, from_branch: str = "main"
    ) -> bool:
        """Create a new branch from an existing one."""
        if not HAS_GITHUB or not self.client:
            logger.warning("Simulating branch creation.")
            return True

        try:
            repo = self.client.get_repo(repo_name)
            source = repo.get_branch(from_branch)
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)
            logger.info(f"Branch '{branch_name}' created from '{from_branch}'")
            return True
        except GithubException as e:
            logger.error(f"Failed to create branch: {e}")
            return False

    async def create_pr(
        self, repo_name: str, branch: str, title: str, description: str, base: str = "main"
    ) -> Dict[str, Any]:
        """Create a pull request."""
        if not HAS_GITHUB or not self.client:
            return {
                "url": f"https://github.com/{repo_name}/pull/mock",
                "number": 0,
                "status": "mocked",
            }

        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.create_pull(title=title, body=description, head=branch, base=base)
            return {"url": pr.html_url, "number": pr.number, "status": "created"}
        except GithubException as e:
            logger.error(f"PR creation failed: {e}")
            return {"url": "", "number": 0, "status": f"error: {e}"}

    async def add_comment(self, repo_name: str, pr_number: int, body: str) -> bool:
        """Add a comment to a PR or Issue."""
        if not HAS_GITHUB or not self.client:
            return True

        try:
            repo = self.client.get_repo(repo_name)
            issue = repo.get_issue(pr_number)
            issue.create_comment(body)
            return True
        except GithubException as e:
            logger.error(f"Failed to add comment: {e}")
            return False

    async def handle_webhook_comment(self, payload: dict) -> dict:
        """Process an incoming GitHub PR comment payload (webhook)."""
        action = payload.get("action")
        comment = payload.get("comment", {}).get("body", "")

        if "@openswe" in comment:
            logger.info("Triggering orchestrator for GitHub comment")
            return {"status": "queued", "message": "Feedback received"}

        return {"status": "ignored"}
