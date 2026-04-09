import logging
import time
from typing import Dict

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Prometheus Metrics
WORKFLOW_LATENCY = Histogram("ai_dev_os_workflow_latency_seconds", "Latency of AI Dev OS workflows")
WORKFLOW_COUNT = Counter(
    "ai_dev_os_workflow_total", "Total count of AI Dev OS workflows", ["status"]
)
TOKEN_USAGE = Counter("ai_dev_os_tokens_total", "Total tokens used", ["model"])
COST_ESTIMATE = Counter("ai_dev_os_cost_dollars", "Estimated cost in dollars", ["model"])
ACTIVE_AGENTS = Gauge("ai_dev_os_active_agents", "Number of currently active agents")


class MetricsManager:
    """
    Manages operational metrics and monitoring for AI Dev OS.
    """

    def __init__(self):
        self.start_times: Dict[str, float] = {}

    def start_workflow(self, workflow_id: str):
        """Track the start of a workflow."""
        self.start_times[workflow_id] = time.time()
        logger.info(f"Monitoring started for workflow: {workflow_id}")

    def end_workflow(self, workflow_id: str, status: str = "success"):
        """Track the end of a workflow and record metrics."""
        if workflow_id in self.start_times:
            latency = time.time() - self.start_times[workflow_id]
            WORKFLOW_LATENCY.observe(latency)
            WORKFLOW_COUNT.labels(status=status).inc()
            logger.info(
                f"Workflow {workflow_id} ended with status {status}. Latency: {latency:.2f}s"
            )
            del self.start_times[workflow_id]

    def record_token_usage(self, model: str, tokens: int):
        """Record token usage and estimate cost."""
        TOKEN_USAGE.labels(model=model).inc(tokens)

        # Simple cost estimation (Claude 3.5 Sonnet: $3/1M input, $15/1M output)
        # For simplicity, we use an average rate of $10 per 1M tokens
        cost = (tokens / 1_000_000) * 10
        COST_ESTIMATE.labels(model=model).inc(cost)

        logger.debug(f"Recorded {tokens} tokens for model {model}. Est cost: ${cost:.4f}")

    def update_active_agents(self, count: int):
        """Update the gauge for active agents."""
        ACTIVE_AGENTS.set(count)


def setup_structured_logging():
    """Setup standard logging as per existing logic."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        logHandler = logging.StreamHandler()
        logHandler.setFormatter(formatter)
        logger.addHandler(logHandler)
    return logger
