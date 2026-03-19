import logging

logger = logging.getLogger(__name__)

class GithubIntegration:
    """
    Handles GitHub PR webhooks and Issue comments for AI Dev OS.
    """
    
    def __init__(self, webhook_secret: str):
        self.webhook_secret = webhook_secret
        
    async def handle_comment(self, payload: dict) -> dict:
        """
        Process an incoming GitHub PR comment payload.
        """
        action = payload.get("action")
        logger.info(f"Received GitHub comment action: {action}")
        
        comment = payload.get("comment", {}).get("body", "")
        
        if "@openswe" in comment:
            logger.info("Triggering orchestrator for GitHub comment")
            return {"status": "queued", "message": "Addressing feedback"}
            
        return {"status": "ignored"}
