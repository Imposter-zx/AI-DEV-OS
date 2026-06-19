from ai_dev_os.utils.metrics import IntegrationMetricsCollector, metrics_collector


def test_metrics_singleton():
    collector1 = IntegrationMetricsCollector()
    collector2 = IntegrationMetricsCollector()
    assert collector1 is collector2
    assert collector1 is metrics_collector


def test_record_success_metrics():
    metrics_collector.reset_metrics()
    metrics_collector.record_success("github", "create_pr", 0.5)

    metrics = metrics_collector.get_metrics("github")
    assert metrics["success_count"] == 1
    assert metrics["total_operations"] == 1
    assert metrics["average_latency"] == 0.5
    assert "create_pr" in metrics["operations"]


def test_record_failure_metrics():
    metrics_collector.reset_metrics()
    metrics_collector.record_failure("slack", "post_message", 0.1, "Timeout")

    metrics = metrics_collector.get_metrics("slack")
    assert metrics["failure_count"] == 1
    assert metrics["success_rate"] == 0.0
    assert metrics["operations"]["post_message"]["failure_count"] == 1


def test_get_health_status_transitions():
    metrics_collector.reset_metrics()
    # No metrics = healthy by default
    assert metrics_collector.get_health_status()["status"] == "healthy"

    # 100% success = healthy
    metrics_collector.record_success("test", "op", 0.1)
    assert metrics_collector.get_health_status()["integrations"]["test"]["status"] == "healthy"

    # < 80% success = unhealthy
    for _ in range(5):
        metrics_collector.record_failure("test", "op", 0.1, "Error")

    status = metrics_collector.get_health_status()
    assert status["integrations"]["test"]["status"] == "unhealthy"
    assert status["status"] == "unhealthy"


def test_reset_specific_integration():
    metrics_collector.reset_metrics()
    metrics_collector.record_success("github", "op", 0.1)
    metrics_collector.record_success("slack", "op", 0.1)

    metrics_collector.reset_metrics("github")
    assert metrics_collector.get_metrics("github")["total_operations"] == 0
    assert metrics_collector.get_metrics("slack")["total_operations"] == 1


def test_get_all_metrics():
    metrics_collector.reset_metrics()
    metrics_collector.record_success("github", "op", 0.1)
    metrics_collector.record_success("slack", "op", 0.1)

    all_metrics = metrics_collector.get_metrics()
    assert "github" in all_metrics
    assert "slack" in all_metrics
