import logging

import httpx

from ai_dev_os.utils.error_handling import with_retry

logger = logging.getLogger(__name__)


class LinearIntegration:
    """
    Handles Linear integration for AI Dev OS.
    """

    def __init__(self, api_key: str):
        if not api_key or api_key.strip() == "":
            raise ValueError("CRITICAL SECURITY ERROR: Linear API key is missing or empty.")
        self.api_key = api_key
        self.api_url = "https://api.linear.app/graphql"

    @with_retry(max_retries=3)
    async def create_issue(self, team_id: str, title: str, description: str) -> dict:
        """
        Create an issue in Linear.
        """
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

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url, json={"query": query, "variables": variables}, headers=headers
            )
            response.raise_for_status()
            data = response.json()
            issue = data.get("data", {}).get("issueCreate", {}).get("issue", {})
            logger.info(f"Linear issue created: {issue.get('id')}")
            return issue

    @with_retry(max_retries=3)
    async def update_issue_status(self, issue_id: str, status: str) -> bool:
        """
        Update the status of a Linear issue.
        """
        query = """
        mutation IssueUpdate($id: String!, $state: String!) {
            issueUpdate(id: $id, input: {stateId: $state}) {
                success
            }
        }
        """
        variables = {"id": issue_id, "state": status}
        headers = {"Authorization": self.api_key, "Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url, json={"query": query, "variables": variables}, headers=headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("issueUpdate", {}).get("success", False)

    async def handle_issue(self, payload: dict) -> dict:
        """
        Process an incoming Linear webhook payload.
        """
        action = payload.get("action")
        data = payload.get("data", {})
        title = data.get("title", "")
        description = data.get("description", "")

        if "@openswe" in title or "@openswe" in description:
            logger.info(f"Triggering orchestrator for Linear issue: {data.get('id')}")
            return {"status": "processing", "message": f"Processing Linear issue {data.get('id')}"}

        return {"status": "ignored"}
