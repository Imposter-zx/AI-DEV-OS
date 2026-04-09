import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ContextManager:
    """Tracks token usage and manages context window for AI Dev OS workflows."""

    def __init__(self, model_name: str = "gpt-4"):
        # Simple fallback: estimate tokens as ~4 characters per token
        # This avoids the tiktoken dependency which is problematic to install
        self.char_per_token = 4.0
        self.workflow_usage: Dict[str, int] = {}
        self.agent_usage: Dict[str, int] = {}

    def count_tokens(self, text: str) -> int:
        """Count tokens in a string using simple approximation."""
        if not text:
            return 0
        # Simple approximation: ~4 characters per token
        return len(text) // int(self.char_per_token)

    def track_usage(self, workflow_id: str, agent_id: str, tokens: int):
        """Track token usage for a workflow and agent."""
        self.workflow_usage[workflow_id] = self.workflow_usage.get(workflow_id, 0) + tokens
        self.agent_usage[agent_id] = self.agent_usage.get(agent_id, 0) + tokens
        logger.debug(f"Tracked {tokens} tokens for WF {workflow_id}, Agent {agent_id}")

    def get_usage_percentage(self, workflow_id: str, limit: int) -> float:
        """Get the percentage of the context window used."""
        used = self.workflow_usage.get(workflow_id, 0)
        return (used / limit) * 100 if limit > 0 else 0.0

    def should_summarize(self, workflow_id: str, limit: int, threshold: float = 90.0) -> bool:
        """Determine if a workflow should be summarized based on capacity."""
        return self.get_usage_percentage(workflow_id, limit) >= threshold

    def generate_summary_prompt(self, logs: List[str]) -> str:
        """Generate a prompt for the model to summarize its own context."""
        combined_logs = "\n".join(logs[-50:])  # Last 50 logs for context
        return f"""
        CRITICAL: Context window almost full (90%+).
        Please provide a concise summary of the work done so far,
        outstanding tasks, and current state. This summary will be used
        to reset the context window.

        Previous history:
        {combined_logs}
        """
