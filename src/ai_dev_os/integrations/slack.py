import logging
from typing import Any, Dict, List, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class SlackIntegration:
    """
    Handles Slack integration for AI Dev OS using slack-sdk.
    """

    def __init__(self, token: str):
        if not token or token.strip() == "":
            raise ValueError("CRITICAL SECURITY ERROR: Slack token is missing or empty.")
        self.token = token
        self.client = WebClient(token=token)

    async def send_message(
        self,
        channel: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a message to Slack, optionally in a thread.
        """
        kwargs = {"channel": channel}
        if text:
            kwargs["text"] = text
        if blocks:
            kwargs["blocks"] = blocks
        if thread_ts:
            kwargs["thread_ts"] = thread_ts

        try:
            response = self.client.chat_postMessage(**kwargs)  # type: ignore
            return {"status": "success", "ts": response["ts"]}
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {"status": "error", "message": str(e)}

    async def handle_message(self, payload: dict) -> dict:
        """
        Process an incoming Slack message (event).
        """
        text = payload.get("text", "")
        if "@openswe" in text:
            logger.info(f"Triggering orchestrator for request: {text}")
            return {"status": "accepted", "message": "Invoking AI Dev OS"}
        return {"status": "ignored"}

    async def handle_interaction(self, payload: dict) -> dict:
        """
        Process a Slack interactive payload (block_actions).
        """
        payload_type = payload.get("type")
        if payload_type == "block_actions":
            action = payload.get("actions", [{}])[0]
            return {
                "action": action.get("action_id"),
                "value": action.get("value"),
                "channel": payload.get("channel", {}).get("id"),
                "message_ts": payload.get("message", {}).get("ts"),
            }
        return {"status": "unknown_interaction"}
