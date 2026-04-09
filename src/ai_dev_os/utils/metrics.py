"""
Centralized metrics collector for AI Dev OS integrations.
Provides a unified way to collect and report metrics across all integrations.
"""

import logging
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class IntegrationMetricsCollector:
    """
    Singleton metrics collector for tracking integration performance and usage.
    """

    _instance: Optional["IntegrationMetricsCollector"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Prevent re-initialization
        if self._initialized:
            return

        self._initialized = True
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._start_time = time.time()
        logger.info("IntegrationMetricsCollector initialized")

    def record_success(self, integration_name: str, operation: str, latency: float) -> None:
        """
        Record a successful operation.
        """
        with self._lock:
            if integration_name not in self._metrics:
                self._metrics[integration_name] = {
                    "success_count": 0,
                    "failure_count": 0,
                    "total_latency": 0.0,
                    "operations": {},
                    "last_success": None,
                    "last_failure": None,
                    "start_time": self._start_time,
                }

            metrics = self._metrics[integration_name]
            metrics["success_count"] += 1
            metrics["total_latency"] += latency
            metrics["last_success"] = time.time()

            # Track operation-specific metrics
            if operation not in metrics["operations"]:
                metrics["operations"][operation] = {
                    "count": 0,
                    "total_latency": 0.0,
                    "success_count": 0,
                    "failure_count": 0,
                }

            op_metrics = metrics["operations"][operation]
            op_metrics["count"] += 1
            op_metrics["success_count"] += 1
            op_metrics["total_latency"] += latency

            logger.debug(
                f"Recorded success for {integration_name}.{operation} (latency: {latency:.3f}s)"
            )

    def record_failure(
        self, integration_name: str, operation: str, latency: float, error: str = ""
    ) -> None:
        """
        Record a failed operation.
        """
        with self._lock:
            if integration_name not in self._metrics:
                self._metrics[integration_name] = {
                    "success_count": 0,
                    "failure_count": 0,
                    "total_latency": 0.0,
                    "operations": {},
                    "last_success": None,
                    "last_failure": None,
                    "start_time": self._start_time,
                }

            metrics = self._metrics[integration_name]
            metrics["failure_count"] += 1
            metrics["total_latency"] += latency
            metrics["last_failure"] = time.time()

            # Track operation-specific metrics
            if operation not in metrics["operations"]:
                metrics["operations"][operation] = {
                    "count": 0,
                    "total_latency": 0.0,
                    "success_count": 0,
                    "failure_count": 0,
                }

            op_metrics = metrics["operations"][operation]
            op_metrics["count"] += 1
            op_metrics["failure_count"] += 1
            op_metrics["total_latency"] += latency

            logger.debug(
                f"Recorded failure for {integration_name}.{operation} (latency: {latency:.3f}s, error: {error})"
            )

    def get_metrics(self, integration_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metrics for a specific integration or all integrations.
        """
        with self._lock:
            if integration_name:
                if integration_name not in self._metrics:
                    return {}

                metrics = self._metrics[integration_name].copy()
                # Calculate derived metrics
                total_ops = metrics["success_count"] + metrics["failure_count"]
                metrics["total_operations"] = total_ops
                metrics["success_rate"] = (
                    (metrics["success_count"] / total_ops * 100) if total_ops > 0 else 0.0
                )
                metrics["average_latency"] = (
                    (metrics["total_latency"] / total_ops) if total_ops > 0 else 0.0
                )
                metrics["uptime"] = time.time() - metrics["start_time"]

                # Process operation metrics
                if "operations" in metrics:
                    for op_name, op_metrics in metrics["operations"].items():
                        op_total = op_metrics["success_count"] + op_metrics["failure_count"]
                        op_metrics["total_operations"] = op_total
                        op_metrics["success_rate"] = (
                            (op_metrics["success_count"] / op_total * 100) if op_total > 0 else 0.0
                        )
                        op_metrics["average_latency"] = (
                            (op_metrics["total_latency"] / op_total) if op_total > 0 else 0.0
                        )

                return metrics
            else:
                # Return all metrics
                all_metrics = {}
                for name, metrics in self._metrics.items():
                    all_metrics[name] = self.get_metrics(name)
                return all_metrics

    def reset_metrics(self, integration_name: Optional[str] = None) -> None:
        """
        Reset metrics for a specific integration or all integrations.
        """
        with self._lock:
            if integration_name:
                if integration_name in self._metrics:
                    self._metrics[integration_name] = {
                        "success_count": 0,
                        "failure_count": 0,
                        "total_latency": 0.0,
                        "operations": {},
                        "last_success": None,
                        "last_failure": None,
                        "start_time": time.time(),
                    }
                    logger.info(f"Reset metrics for {integration_name}")
            else:
                self._metrics.clear()
                self._start_time = time.time()
                logger.info("Reset all integration metrics")

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall health status of all integrations.
        """
        with self._lock:
            health = {
                "status": "healthy",
                "timestamp": time.time(),
                "uptime": time.time() - self._start_time,
                "integrations": {},
            }

            unhealthy_count = 0
            total_integrations = len(self._metrics)

            for name, metrics in self._metrics.items():
                total_ops = metrics["success_count"] + metrics["failure_count"]
                success_rate = (
                    (metrics["success_count"] / total_ops * 100) if total_ops > 0 else 100.0
                )

                integration_health = {
                    "status": (
                        "healthy"
                        if success_rate >= 95.0
                        else "degraded" if success_rate >= 80.0 else "unhealthy"
                    ),
                    "success_rate": success_rate,
                    "total_operations": total_ops,
                    "last_success": metrics.get("last_success"),
                    "last_failure": metrics.get("last_failure"),
                }

                if integration_health["status"] != "healthy":
                    unhealthy_count += 1

                health["integrations"][name] = integration_health

            # Overall health determination
            if unhealthy_count == 0:
                health["status"] = "healthy"
            elif unhealthy_count < total_integrations / 2:
                health["status"] = "degraded"
            else:
                health["status"] = "unhealthy"

            return health


# Global instance for easy access
metrics_collector = IntegrationMetricsCollector()
