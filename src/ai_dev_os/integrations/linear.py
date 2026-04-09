import logging
import time

import httpx

from ai_dev_os.utils.error_handling import with_retry
from ai_dev_os.utils.metrics import metrics_collector

logger = logging.getLogger(__name__)


class LinearIntegration:
    """
    Handles Linear integration for AI Dev OS.
    """

    def __init__(self, api_key: str):
        if not api_key or api_key.strip() == "":
            raise ValueError(
                "CRITICAL SECURITY ERROR: Linear API key is missing or empty."
            )
        self.api_key = api_key
        self.api_url = "https://api.linear.app/graphql"
        self.integration_name = "linear"

    @with_retry(max_retries=3)
    async def create_issue(self, team_id: str, title: str, description: str) -> dict:
        """
        Create an issue in Linear.
        """
        start_time = time.time()
        query = """
        mutation IssueCreate($title: String!, $description: String, $teamId: String!) {
            issueCreate(input: {title: $title, description: $description, teamId: $teamId}) {
                success
                issue { id url }
            }
        }
        """
        variables = {"title": title, "description": description, "teamId": team_id}
        headers = {"Authorization": self.api_key, "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json={"query": query, "variables": variables},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                issue = data.get("data", {}).get("issueCreate", {}).get("issue", {})
                metrics_collector.record_success(
                    self.integration_name, "create_issue", time.time() - start_time
                )
                logger.info(
                    f"Linear issue created: {issue.get('id')} in {time.time() - start_time:.2f}s"
                )
                return {"issue": issue, "latency": time.time() - start_time}
        except Exception as e:
            metrics_collector.record_failure(
                self.integration_name, "create_issue", time.time() - start_time, str(e)
            )
            logger.error(f"Failed to create Linear issue: {e}")
            return {"error": str(e), "latency": time.time() - start_time}

    @with_retry(max_retries=3)
    async def update_issue_status(self, issue_id: str, status: str) -> dict:
        """
        Update the status of a Linear issue.
        """
        start_time = time.time()
        query = """
        mutation IssueUpdate($id: String!, $state: String!) {
            issueUpdate(id: $id, input: {stateId: $state}) {
                success
            }
        }
        """
        variables = {"id": issue_id, "state": status}
        headers = {"Authorization": self.api_key, "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json={"query": query, "variables": variables},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                metrics_collector.record_success(
                    self.integration_name,
                    "update_issue_status",
                    time.time() - start_time,
                )
                success = (
                    data.get("data", {}).get("issueUpdate", {}).get("success", False)
                )
                logger.info(
                    f"Linear issue {issue_id} status updated in {time.time() - start_time:.2f}s"
                )
                return {"success": success, "latency": time.time() - start_time}
        except Exception as e:
            metrics_collector.record_failure(
                self.integration_name,
                "update_issue_status",
                time.time() - start_time,
                str(e),
            )
            logger.error(f"Failed to update Linear issue status: {e}")
            return {
                "success": False,
                "error": str(e),
                "latency": time.time() - start_time,
            }

    async def handle_issue(self, payload: dict) -> dict:
        """
        Process an incoming Linear webhook payload.
        """
        payload.get("action")
        data = payload.get("data", {})
        title = data.get("title", "")
        description = data.get("description", "")

        if "@openswe" in title or "@openswe" in description:
            logger.info(f"Triggering orchestrator for Linear issue: {data.get('id')}")
            return {
                "status": "processing",
                "message": f"Processing Linear issue {data.get('id')}",
            }

        return {"status": "ignored"}
