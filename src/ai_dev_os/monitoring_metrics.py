"""
Prometheus monitoring metrics for AI Dev OS.

Tracks workflow execution, context usage, and agent performance.
"""

import logging
import time

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram, start_http_server

    # ─── Metrics ─────────────────────────────────────────────────────

    workflow_started = Counter(
        "aidevos_workflows_started_total",
        "Total number of workflows started",
    )

    workflow_completed = Counter(
        "aidevos_workflows_completed_total",
        "Total number of workflows completed",
        ["status"],
    )

    workflow_duration = Histogram(
        "aidevos_workflow_duration_seconds",
        "Workflow duration in seconds",
        buckets=[10, 30, 60, 120, 300, 600, 1800],
    )

    context_usage = Histogram(
        "aidevos_context_usage_percent",
        "Context usage percentage at workflow end",
        buckets=[10, 25, 50, 75, 90, 95, 100],
    )

    agent_executions = Counter(
        "aidevos_agent_executions_total",
        "Total agent executions",
        ["agent_name", "role"],
    )

    HAS_PROMETHEUS = True

except ImportError:
    logger.info("prometheus_client not installed. Metrics collection disabled.")
    HAS_PROMETHEUS = False


def start_metrics_server(port: int = 8000):
    """Start the Prometheus metrics HTTP server."""
    if HAS_PROMETHEUS:
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
    else:
        logger.warning("Cannot start metrics server: prometheus_client not installed.")


class MonitoredOrchestrator:
    """
    Wrapper around AIDevOSOrchestrator that adds Prometheus metrics.

    Usage:
        from ai_dev_os.core import AIDevOSOrchestrator
        monitored = MonitoredOrchestrator(AIDevOSOrchestrator())
        state = await monitored.run("Build auth module")
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    async def run(self, request: str):
        """Run a workflow with metrics tracking."""
        if HAS_PROMETHEUS:
            workflow_started.inc()

        start_time = time.time()

        try:
            state = await self.orchestrator.run(request)

            if HAS_PROMETHEUS:
                workflow_completed.labels(status="success").inc()
                context_usage.observe(state.context_usage)

                for config in state.subagent_configs:
                    agent_executions.labels(
                        agent_name=config.name,
                        role=config.role,
                    ).inc()

            return state

        except Exception:
            if HAS_PROMETHEUS:
                workflow_completed.labels(status="error").inc()
            raise

        finally:
            duration = time.time() - start_time
            if HAS_PROMETHEUS:
                workflow_duration.observe(duration)
            logger.info(f"Workflow completed in {duration:.2f}s")
