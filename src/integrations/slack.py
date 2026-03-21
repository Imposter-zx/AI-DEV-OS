import logging
import httpx
from ai_dev_os.utils.error_handling import with_retry

logger = logging.getLogger(__name__)

class SlackIntegration:
    """
    Handles Slack incoming webhooks and events for AI Dev OS.
    """
    
    def __init__(self, token: str):
        self.token = token
        
    @with_retry(max_retries=3)
    async def send_notification(self, message: str) -> dict:
        """
        Send a real notification to a Slack webhook.
        """
        async with httpx.AsyncClient() as client:
            payload = {"text": message}
            response = await client.post(self.token, json=payload)
            response.raise_for_status()
            logger.info(f"Slack notification sent: {message}")
            return {"status": "success"}

    async def handle_message(self, payload: dict) -> dict:
        """
        Process an incoming Slack conversation message.
        """
        logger.info(f"Received Slack payload: {payload.get('type')}")
        text = payload.get("text", "")
        if "@openswe" in text:
            # Here we would invoke AIDevOSOrchestrator
            logger.info(f"Triggering orchestrator for request: {text}")
            return {"status": "accepted", "message": "Invoking AI Dev OS"}
            
        return {"status": "ignored", "message": "No trigger found"}
