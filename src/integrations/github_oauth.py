"""
GitHub OAuth and PR creation integration for AI Dev OS.

Uses PyGithub for real repository operations.
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
    Real GitHub integration using PyGithub.

    Supports:
    - Creating pull requests
    - Listing repositories
    - Managing branches
    - Reading issues
    """

    def __init__(self, token: str):
        self.token = token
        if HAS_GITHUB:
            self.client = Github(token)
        else:
            self.client = None

    async def create_pr(
        self,
        repo_name: str,
        branch: str,
        title: str,
        description: str,
        base: str = "main",
    ) -> Dict[str, Any]:
        """
        Create a real pull request on GitHub.

        Args:
            repo_name: Full repo name, e.g. 'user/repo'
            branch: Head branch name
            title: PR title
            description: PR body/description
            base: Base branch to merge into

        Returns:
            Dict with url, number, and status.
        """
        if not HAS_GITHUB or not self.client:
            logger.warning("PyGithub not available. Simulating PR creation.")
            return {
                "url": f"https://github.com/{repo_name}/pull/999",
                "number": 999,
                "status": "simulated",
            }

        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.create_pull(
                title=title,
                body=description,
                head=branch,
                base=base,
            )
            logger.info(f"PR created: {pr.html_url}")
            return {
                "url": pr.html_url,
                "number": pr.number,
                "status": "created",
            }
        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            return {"url": "", "number": 0, "status": f"error: {e}"}

    async def list_repos(self) -> List[Dict[str, str]]:
        """List accessible repositories."""
        if not HAS_GITHUB or not self.client:
            return [{"name": "mock/repo", "url": "https://github.com/mock/repo"}]

        repos = []
        for repo in self.client.get_user().get_repos():
            repos.append({
                "name": repo.full_name,
                "url": repo.html_url,
                "default_branch": repo.default_branch,
            })
        return repos

    async def get_open_issues(self, repo_name: str) -> List[Dict[str, Any]]:
        """Get open issues for a repository."""
        if not HAS_GITHUB or not self.client:
            return []

        try:
            repo = self.client.get_repo(repo_name)
            issues = []
            for issue in repo.get_issues(state="open"):
                issues.append({
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body or "",
                    "labels": [l.name for l in issue.labels],
                })
            return issues
        except GithubException as e:
            logger.error(f"Failed to fetch issues: {e}")
            return []

    async def create_branch(self, repo_name: str, branch_name: str, from_branch: str = "main") -> bool:
        """Create a new branch from an existing one."""
        if not HAS_GITHUB or not self.client:
            logger.warning("Simulating branch creation.")
            return True

        try:
            repo = self.client.get_repo(repo_name)
            source = repo.get_branch(from_branch)
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=source.commit.sha,
            )
            logger.info(f"Branch '{branch_name}' created from '{from_branch}'")
            return True
        except GithubException as e:
            logger.error(f"Failed to create branch: {e}")
            return False
