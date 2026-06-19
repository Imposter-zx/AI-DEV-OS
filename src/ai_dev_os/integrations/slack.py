import logging
import time
from typing import Any, Dict, List, Optional

from ai_dev_os.utils.circuit_breaker import breaker_registry
from ai_dev_os.utils.health import create_integration_health_check, health
from ai_dev_os.utils.metrics import metrics_collector

logger = logging.getLogger(__name__)

_slack_breaker = breaker_registry.get_or_create("slack", failure_threshold=5, recovery_timeout=30.0)


class SlackIntegration:
    """
    Handles Slack integration for AI Dev OS using slack-sdk.
    """

    def __init__(self, token: str):
        if not token or token.strip() == "":
            raise ValueError("CRITICAL SECURITY ERROR: Slack token is missing or empty.")
        self.token = token
        self.integration_name = "slack"
        try:
            from slack_sdk import WebClient

            self.client = WebClient(token=token)
            self._slack_available = True
        except ImportError:
            logger.warning("slack-sdk not installed. Slack integration will be mocked.")
            self.client = None
            self._slack_available = False

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
        start_time = time.time()
        kwargs: Dict[str, Any] = {"channel": channel}
        if text:
            kwargs["text"] = text
        if blocks:
            kwargs["blocks"] = blocks
        if thread_ts:
            kwargs["thread_ts"] = thread_ts

        if not self._slack_available:
            metrics_collector.record_success(
                self.integration_name, "send_message", time.time() - start_time
            )
            return {
                "status": "success",
                "ts": "mocked",
                "latency": time.time() - start_time,
                "message": "Slack message sent (simulated - slack-sdk not installed)",
            }

        try:
            response = self.client.chat_postMessage(**kwargs)  # type: ignore
            metrics_collector.record_success(
                self.integration_name, "send_message", time.time() - start_time
            )
            logger.info(f"Slack message sent to {channel} in {time.time() - start_time:.2f}s")
            return {
                "status": "success",
                "ts": response["ts"],
                "latency": time.time() - start_time,
            }
        except Exception as e:
            # Try to detect SlackApiError without importing it
            error_str = str(e)
            if "SlackApiError" in type(e).__name__:
                error_detail = getattr(e, "response", {}).get("error", str(e))
                metrics_collector.record_failure(
                    self.integration_name, "send_message", time.time() - start_time, error_str
                )
                logger.error(f"Slack API error: {error_detail}")
            else:
                metrics_collector.record_failure(
                    self.integration_name, "send_message", time.time() - start_time, error_str
                )
                logger.error(f"Unexpected error sending Slack message: {e}")
            return {
                "status": "error",
                "message": error_str,
                "latency": time.time() - start_time,
            }

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


health.register_check("slack", create_integration_health_check("slack"))
