import logging
import httpx
from ai_dev_os.utils.error_handling import with_retry

logger = logging.getLogger(__name__)

class LinearIntegration:
    """
    Handles Linear webhooks and API for AI Dev OS.
    """
    
    def __init__(self, webhook_secret: str):
        if not webhook_secret or webhook_secret.strip() == "":
            raise ValueError("CRITICAL SECURITY ERROR: Linear webhook secret is missing or empty.")
        self.webhook_secret = webhook_secret
        self.api_url = "https://api.linear.app/graphql"
        
    @with_retry(max_retries=3)
    async def create_issue(self, title: str, description: str, team_id: str) -> dict:
        """
        Create a true issue in Linear via GraphQL.
        """
        query = '''
        mutation IssueCreate($title: String!, $description: String, $teamId: String!) {
            issueCreate(input: {title: $title, description: $description, teamId: $teamId}) {
                success
                issue { id title }
            }
        }
        '''
        variables = {"title": title, "description": description, "teamId": team_id}
        headers = {"Authorization": self.webhook_secret}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, json={"query": query, "variables": variables}, headers=headers)
            response.raise_for_status()
            logger.info(f"Linear issue created: {title}")
            return response.json()

    async def handle_issue(self, payload: dict) -> dict:
        """
        Process an incoming Linear issue payload.
        """
        logger.info(f"Received Linear action: {payload.get('action')}")
        data = payload.get("data", {})
        title = data.get("title", "")
        
        # In a real app, this parses descriptions to find instructions 
        logger.info(f"Triggering orchestrator for Linear issue: {title}")
        return {"status": "processing", "issue_id": data.get("id")}
