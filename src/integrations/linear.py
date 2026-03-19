import logging

logger = logging.getLogger(__name__)

class LinearIntegration:
    """
    Handles Linear webhooks for AI Dev OS.
    """
    
    def __init__(self, webhook_secret: str):
        self.webhook_secret = webhook_secret
        
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
