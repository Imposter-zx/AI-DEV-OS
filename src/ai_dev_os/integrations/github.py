"""
GitHub integration for AI Dev OS.

Handles repository operations, PR creation, and branch management using PyGithub.
"""

import asyncio
import logging
import time
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
            raise ValueError(
                "CRITICAL SECURITY ERROR: GitHub token is missing or empty."
            )
        self.token = token
        self.client = Github(token) if HAS_GITHUB else None
        # Metrics counters
        self.branches_created = 0
        self.prs_created = 0
        self.comments_added = 0
        self.requests_failed = 0
        self.last_error_time: Optional[float] = None

    async def create_branch(
        self, repo_name: str, branch_name: str, from_branch: str = "main"
    ) -> Dict[str, Any]:
        """Create a new branch from an existing one."""
        start_time = time.time()
        if not HAS_GITHUB or not self.client:
            logger.warning("Simulating branch creation.")
            return {
                "status": "success",
                "message": "Branch created (simulated)",
                "latency": time.time() - start_time,
            }

        try:
            repo = self.client.get_repo(repo_name)
            source = repo.get_branch(from_branch)
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)
            self.branches_created += 1
            logger.info(
                f"Branch '{branch_name}' created from '{from_branch}' in {time.time() - start_time:.2f}s"
            )
            return {
                "status": "success",
                "message": f"Branch '{branch_name}' created",
                "latency": time.time() - start_time,
            }
        except GithubException as e:
            self.requests_failed += 1
            self.last_error_time = time.time()
            logger.error(f"Failed to create branch: {e}")
            return {
                "status": "error",
                "message": str(e),
                "latency": time.time() - start_time,
            }
        except Exception as e:
            self.requests_failed += 1
            self.last_error_time = time.time()
            logger.error(f"Unexpected error creating branch: {e}")
            return {
                "status": "error",
                "message": str(e),
                "latency": time.time() - start_time,
            }

    async def create_pr(
        self,
        repo_name: str,
        branch: str,
        title: str,
        description: str,
        base: str = "main",
    ) -> Dict[str, Any]:
        """Create a pull request."""
        start_time = time.time()
        if not HAS_GITHUB or not self.client:
            return {
                "url": f"https://github.com/{repo_name}/pull/mock",
                "number": 0,
                "status": "mocked",
                "latency": time.time() - start_time,
            }

        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.create_pull(title=title, body=description, head=branch, base=base)
            self.prs_created += 1
            logger.info(
                f"PR #{pr.number} created: {pr.title} in {time.time() - start_time:.2f}s"
            )
            return {
                "url": pr.html_url,
                "number": pr.number,
                "status": "created",
                "latency": time.time() - start_time,
            }
        except GithubException as e:
            self.requests_failed += 1
            self.last_error_time = time.time()
            logger.error(f"PR creation failed: {e}")
            return {
                "url": "",
                "number": 0,
                "status": f"error: {e}",
                "latency": time.time() - start_time,
            }
        except Exception as e:
            self.requests_failed += 1
            self.last_error_time = time.time()
            logger.error(f"Unexpected error creating PR: {e}")
            return {
                "url": "",
                "number": 0,
                "status": f"error: {e}",
                "latency": time.time() - start_time,
            }

    async def add_comment(
        self, repo_name: str, pr_number: int, body: str
    ) -> Dict[str, Any]:
        """Add a comment to a PR or Issue."""
        start_time = time.time()
        if not HAS_GITHUB or not self.client:
            return {
                "status": "success",
                "message": "Comment added (simulated)",
                "latency": time.time() - start_time,
            }

        try:
            repo = self.client.get_repo(repo_name)
            issue = repo.get_issue(pr_number)
            issue.create_comment(body)
            self.comments_added += 1
            logger.info(
                f"Comment added to issue #{pr_number} in {time.time() - start_time:.2f}s"
            )
            return {
                "status": "success",
                "message": "Comment added",
                "latency": time.time() - start_time,
            }
        except GithubException as e:
            self.requests_failed += 1
            self.last_error_time = time.time()
            logger.error(f"Failed to add comment: {e}")
            return {
                "status": "error",
                "message": str(e),
                "latency": time.time() - start_time,
            }
        except Exception as e:
            self.requests_failed += 1
            self.last_error_time = time.time()
            logger.error(f"Unexpected error adding comment: {e}")
            return {
                "status": "error",
                "message": str(e),
                "latency": time.time() - start_time,
            }

    async def handle_webhook_comment(self, payload: dict) -> dict:
        """Process an incoming GitHub PR comment payload (webhook)."""
        action = payload.get("action")
        comment = payload.get("comment", {}).get("body", "")

        if "@openswe" in comment:
            logger.info("Triggering orchestrator for GitHub comment")
            return {"status": "queued", "message": "Feedback received"}

        return {"status": "ignored"}

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get integration metrics.
        """
        total_requests = (
            self.branches_created
            + self.prs_created
            + self.comments_added
            + self.requests_failed
        )
        success_rate = (
            (
                (self.branches_created + self.prs_created + self.comments_added)
                / total_requests
                * 100
            )
            if total_requests > 0
            else 0.0
        )
        return {
            "branches_created": self.branches_created,
            "prs_created": self.prs_created,
            "comments_added": self.comments_added,
            "requests_failed": self.requests_failed,
            "success_rate": success_rate,
            "last_error_time": self.last_error_time,
        }

    def reset_metrics(self) -> None:
        """
        Reset integration metrics.
        """
        self.branches_created = 0
        self.prs_created = 0
        self.comments_added = 0
        self.requests_failed = 0
        self.last_error_time = None
