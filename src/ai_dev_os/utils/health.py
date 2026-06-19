"""
Integration health check utilities.
Provides health status for all external service integrations.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ai_dev_os.utils.metrics import metrics_collector

logger = logging.getLogger(__name__)


class HealthStatus:
    def __init__(self):
        self.checks: Dict[str, Dict[str, Any]] = {}
        self.start_time = datetime.now(timezone.utc)

    def register_check(self, name: str, check_func):
        """Register a health check function."""
        self.checks[name] = {
            "function": check_func,
            "last_run": None,
            "last_result": None,
        }

    def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check."""
        if name not in self.checks:
            return {
                "name": name,
                "status": "error",
                "error": f"No check registered for '{name}'",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        check = self.checks[name]
        try:
            result = check["function"]()
            status = "healthy" if result.get("healthy", False) else "degraded"
            check["last_run"] = datetime.now(timezone.utc).isoformat()
            check["last_result"] = {"status": status, **result}
            return {"name": name, "status": status, "timestamp": check["last_run"], **result}
        except Exception as e:
            logger.error(f"Health check '{name}' failed: {e}")
            check["last_result"] = {"status": "unhealthy", "error": str(e)}
            return {
                "name": name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def run_all(self) -> List[Dict[str, Any]]:
        """Run all registered health checks."""
        return [self.run_check(name) for name in self.checks]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all health check results."""
        results = self.run_all()
        healthy = sum(1 for r in results if r.get("status") == "healthy")
        degraded = sum(1 for r in results if r.get("status") == "degraded")
        unhealthy = sum(1 for r in results if r.get("status") == "unhealthy")

        return {
            "service": "ai-dev-os",
            "status": "healthy" if unhealthy == 0 else "degraded",
            "uptime": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
            "checks": {
                "total": len(results),
                "healthy": healthy,
                "degraded": degraded,
                "unhealthy": unhealthy,
            },
            "details": results,
            "metrics_summary": {
                integration: {k: v for k, v in data.items() if k != "operations"}
                for integration, data in metrics_collector.get_metrics().items()
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


health = HealthStatus()


def create_integration_health_check(integration_name: str):
    """Create a health check function for an integration."""

    def check():
        metrics = metrics_collector.get_metrics(integration_name)
        if not metrics:
            return {"healthy": False, "error": f"No metrics for '{integration_name}'"}

        failure_rate = metrics.get("failure_rate", 0)
        healthy = failure_rate < 50.0

        return {
            "healthy": healthy,
            "total_calls": metrics.get("total_calls", 0),
            "success_count": metrics.get("success_count", 0),
            "failure_count": metrics.get("failure_count", 0),
            "failure_rate": failure_rate,
            "average_latency": metrics.get("average_latency", 0),
        }

    return check
