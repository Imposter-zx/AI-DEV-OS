"""Tests for all enhanced integrations."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from ai_dev_os.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    CircuitBreakerRegistry,
)
from ai_dev_os.utils.health import HealthStatus, create_integration_health_check
from ai_dev_os.utils.metrics import IntegrationMetricsCollector


@pytest.fixture
def metrics():
    collector = IntegrationMetricsCollector()
    collector._metrics = {}
    collector._start_time = 1000.0
    return collector


# =============================================================================
# Metrics Collector Tests
# =============================================================================


class TestMetricsCollector:
    def test_record_success(self, metrics):
        metrics.record_success("test", "op1", latency=0.5)
        m = metrics.get_metrics("test")
        assert m["success_count"] == 1
        assert m["failure_count"] == 0
        assert m["total_operations"] == 1

    def test_record_failure(self, metrics):
        metrics.record_failure("test", "op1", latency=0.3)
        m = metrics.get_metrics("test")
        assert m["success_count"] == 0
        assert m["failure_count"] == 1
        assert m["success_rate"] == 0.0

    def test_get_nonexistent_returns_empty(self, metrics):
        m = metrics.get_metrics("nonexistent")
        assert m == {}

    def test_record_multiple_operations(self, metrics):
        metrics.record_success("test", "create", latency=0.1)
        metrics.record_success("test", "update", latency=0.2)
        all_m = metrics.get_metrics()
        assert "test" in all_m
        assert all_m["test"]["total_operations"] == 2

    def test_average_latency(self, metrics):
        metrics.record_success("test", "op1", latency=1.0)
        metrics.record_success("test", "op1", latency=3.0)
        m = metrics.get_metrics("test")
        assert m["average_latency"] == 2.0

    def test_singleton_behavior(self):
        m1 = IntegrationMetricsCollector()
        m2 = IntegrationMetricsCollector()
        assert m1 is m2

    def test_get_all_metrics(self, metrics):
        metrics.record_success("slack", "send", 0.1)
        metrics.record_success("linear", "create", 0.2)
        all_m = metrics.get_metrics()
        assert "slack" in all_m
        assert "linear" in all_m

    def test_reset_specific(self, metrics):
        metrics.record_success("slack", "send", 0.1)
        metrics.reset_metrics("slack")
        m = metrics.get_metrics("slack")
        assert m["success_count"] == 0

    def test_reset_all(self, metrics):
        metrics.record_success("slack", "send", 0.1)
        metrics.record_success("linear", "create", 0.2)
        metrics.reset_metrics()
        assert metrics.get_metrics() == {}

    def test_health_status_healthy(self, metrics):
        metrics.record_success("slack", "send", 0.1)
        metrics.record_success("linear", "create", 0.2)
        h = metrics.get_health_status()
        assert h["status"] == "healthy"
        assert h["integrations"]["slack"]["status"] == "healthy"

    def test_health_status_unhealthy(self, metrics):
        for _ in range(10):
            metrics.record_failure("slack", "send", 0.1)
        h = metrics.get_health_status()
        assert h["integrations"]["slack"]["status"] == "unhealthy"


# =============================================================================
# Circuit Breaker Tests
# =============================================================================


class TestCircuitBreaker:
    def test_initial_state(self):
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_successful_call(self):
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
        result = cb.call(lambda: "ok")
        assert result == "ok"
        assert cb.successful_calls == 1

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
        for _ in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

    def test_open_refuses_calls(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60)
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "should not reach")

    def test_half_open_recovers(self, mocker):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=10)

        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        cb.last_failure_time = 100.0

        mocker.patch("ai_dev_os.utils.circuit_breaker.time.time", return_value=120.0)

        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED

    def test_reset(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60)
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_get_state(self):
        cb = CircuitBreaker(name="test", failure_threshold=5, recovery_timeout=30)
        state = cb.get_state()
        assert state["name"] == "test"
        assert state["state"] == "closed"

    def test_half_open_recovers_then_fails_again(self, mocker):
        cb = CircuitBreaker(
            name="test", failure_threshold=1, recovery_timeout=10, half_open_max_calls=3
        )

        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        cb.last_failure_time = 100.0
        mocker.patch("ai_dev_os.utils.circuit_breaker.time.time", return_value=120.0)

        result = cb.call(lambda: "ok1")
        assert result == "ok1"
        assert cb.state == CircuitState.CLOSED

        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail2")))
        except ValueError:
            pass

        assert cb.state == CircuitState.OPEN

    def test_async_call(self):
        cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=60)

        async def good():
            return "ok"

        async def bad():
            raise ValueError("fail")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(cb.call_async(good))
            assert result == "ok"

            for _ in range(2):
                try:
                    loop.run_until_complete(cb.call_async(bad))
                except ValueError:
                    pass

            assert cb.state == CircuitState.OPEN
        finally:
            loop.close()

    def test_registry_singleton(self):
        r1 = CircuitBreakerRegistry()
        r2 = CircuitBreakerRegistry()
        assert r1 is r2

    def test_registry_get_or_create(self):
        registry = CircuitBreakerRegistry()
        cb1 = registry.get_or_create("slack", failure_threshold=3)
        cb2 = registry.get_or_create("slack", failure_threshold=5)
        assert cb1 is cb2
        assert cb1.failure_threshold == 3

    def test_registry_get_all_states(self):
        registry = CircuitBreakerRegistry()
        registry.get_or_create("slack")
        registry.get_or_create("linear")
        states = registry.get_all_states()
        assert "slack" in states
        assert "linear" in states

    def test_registry_reset_all(self):
        registry = CircuitBreakerRegistry()
        cb = registry.get_or_create("test_reset_breaker", failure_threshold=1)

        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        assert cb.state == CircuitState.OPEN
        registry.reset_all()
        assert cb.state == CircuitState.CLOSED


# =============================================================================
# Health Status Tests
# =============================================================================


class TestHealthStatus:
    def test_register_and_run_check(self):
        h = HealthStatus()
        h.register_check("test", lambda: {"healthy": True, "detail": "ok"})
        result = h.run_check("test")
        assert result["status"] == "healthy"
        assert result["detail"] == "ok"

    def test_run_nonexistent_check(self):
        h = HealthStatus()
        result = h.run_check("nonexistent")
        assert result["status"] == "error"

    def test_check_raises_exception(self):
        h = HealthStatus()

        def failing():
            raise RuntimeError("boom")

        h.register_check("fail", failing)
        result = h.run_check("fail")
        assert result["status"] == "unhealthy"
        assert "boom" in result["error"]

    def test_run_all(self):
        h = HealthStatus()
        h.register_check("a", lambda: {"healthy": True})
        h.register_check("b", lambda: {"healthy": False})
        results = h.run_all()
        assert len(results) == 2

    def test_get_summary(self):
        h = HealthStatus()
        h.register_check("ok", lambda: {"healthy": True})
        summary = h.get_summary()
        assert summary["service"] == "ai-dev-os"
        assert "status" in summary
        assert "uptime" in summary

    def test_summary_status_degraded(self):
        h = HealthStatus()
        h.register_check("a", lambda: {"healthy": True})
        h.register_check("b", lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        summary = h.get_summary()
        assert summary["checks"]["unhealthy"] >= 1

    def test_create_integration_health_check(self, mocker):
        mock_metrics = {
            "total_calls": 10,
            "success_count": 9,
            "failure_count": 1,
            "failure_rate": 10.0,
            "average_latency": 0.5,
        }

        mocker.patch(
            "ai_dev_os.utils.metrics.IntegrationMetricsCollector.get_metrics",
            return_value=mock_metrics,
        )

        check_fn = create_integration_health_check("slack")
        result = check_fn()
        assert result["healthy"] is True
        assert result["total_calls"] == 10


# =============================================================================
# Slack Integration Tests
# =============================================================================


class TestSlackIntegration:
    @pytest.fixture
    def integration(self):
        from ai_dev_os.integrations.slack import SlackIntegration

        return SlackIntegration(token="xoxb-fake-token")

    @pytest.mark.asyncio
    async def test_send_message_with_text(self, integration, mocker):
        integration._slack_available = True
        mock_fn = MagicMock(return_value={"ts": "12345.67890"})
        integration.client = MagicMock()
        integration.client.chat_postMessage = mock_fn

        result = await integration.send_message(channel="#test", text="Hello")
        assert result["status"] == "success"
        assert result["ts"] == "12345.67890"
        assert "latency" in result

    @pytest.mark.asyncio
    async def test_send_message_with_blocks(self, integration, mocker):
        integration._slack_available = True
        mock_fn = MagicMock(return_value={"ts": "12345.67890"})
        integration.client = MagicMock()
        integration.client.chat_postMessage = mock_fn
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Hello"}}]

        result = await integration.send_message(channel="#test", blocks=blocks)
        assert result["status"] == "success"
        assert result["ts"] == "12345.67890"

    @pytest.mark.asyncio
    async def test_send_message_in_thread(self, integration, mocker):
        integration._slack_available = True
        mock_fn = MagicMock(return_value={"ts": "12345.67890"})
        integration.client = MagicMock()
        integration.client.chat_postMessage = mock_fn

        result = await integration.send_message(
            channel="#test", text="Reply", thread_ts="123.456"
        )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_send_message_error(self, integration, mocker):
        integration._slack_available = True
        mock_fn = MagicMock(side_effect=Exception("Network error"))
        integration.client = MagicMock()
        integration.client.chat_postMessage = mock_fn

        result = await integration.send_message(channel="#test", text="Hello")
        assert result["status"] == "error"
        assert "latency" in result

    @pytest.mark.asyncio
    async def test_send_message_simulated(self, integration, mocker):
        integration._slack_available = False
        result = await integration.send_message(channel="#test", text="Hello")
        assert result["status"] == "success"
        assert "simulated" in result.get("message", "")

    @pytest.mark.asyncio
    async def test_handle_message_triggers_on_mention(self, integration):
        payload = {"text": "Hey @openswe do something"}
        result = await integration.handle_message(payload)
        assert result["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_handle_message_ignores_others(self, integration):
        payload = {"text": "Just a normal message"}
        result = await integration.handle_message(payload)
        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_handle_interaction_block_actions(self, integration):
        payload = {
            "type": "block_actions",
            "actions": [{"action_id": "btn_1", "value": "clicked"}],
            "channel": {"id": "C123"},
            "message": {"ts": "123.456"},
        }
        result = await integration.handle_interaction(payload)
        assert result["action"] == "btn_1"
        assert result["value"] == "clicked"

    @pytest.mark.asyncio
    async def test_handle_interaction_unknown(self, integration):
        payload = {"type": "view_submission"}
        result = await integration.handle_interaction(payload)
        assert result["status"] == "unknown_interaction"

    def test_empty_token_raises(self):
        from ai_dev_os.integrations.slack import SlackIntegration

        with pytest.raises(ValueError, match="CRITICAL SECURITY ERROR"):
            SlackIntegration(token="")

    def test_whitespace_token_raises(self):
        from ai_dev_os.integrations.slack import SlackIntegration

        with pytest.raises(ValueError, match="CRITICAL SECURITY ERROR"):
            SlackIntegration(token="   ")


# =============================================================================
# Linear Integration Tests
# =============================================================================


class TestLinearIntegration:
    @pytest.fixture
    def integration(self):
        from ai_dev_os.integrations.linear import LinearIntegration

        return LinearIntegration(api_key="lin-api-fake-key")

    @pytest.mark.asyncio
    async def test_create_issue(self, integration, mocker):
        async def mock_post(*args, **kwargs):
            mock = MagicMock()
            mock.status_code = 200
            mock.json.return_value = {
                "data": {
                    "issueCreate": {
                        "success": True,
                        "issue": {"id": "lin-1", "url": "https://..."},
                    }
                }
            }
            return mock

        mocker.patch("httpx.AsyncClient.post", mock_post)

        result = await integration.create_issue(
            team_id="team-1", title="Test Issue", description="Desc"
        )
        assert "issue" in result
        assert result["issue"]["id"] == "lin-1"
        assert "latency" in result

    @pytest.mark.asyncio
    async def test_create_issue_failure(self, integration, mocker):
        async def mock_fail(*args, **kwargs):
            raise Exception("API error")

        mocker.patch("httpx.AsyncClient.post", mock_fail)

        result = await integration.create_issue(
            team_id="team-1", title="Test Issue", description="Desc"
        )
        assert "error" in result
        assert "latency" in result

    @pytest.mark.asyncio
    async def test_update_issue_status(self, integration, mocker):
        async def mock_post(*args, **kwargs):
            mock = MagicMock()
            mock.status_code = 200
            mock.json.return_value = {"data": {"issueUpdate": {"success": True}}}
            return mock

        mocker.patch("httpx.AsyncClient.post", mock_post)

        result = await integration.update_issue_status(issue_id="lin-1", status="Done")
        assert result["success"] is True
        assert "latency" in result

    @pytest.mark.asyncio
    async def test_update_issue_status_failure(self, integration, mocker):
        async def mock_fail(*args, **kwargs):
            raise Exception("API error")

        mocker.patch("httpx.AsyncClient.post", mock_fail)

        result = await integration.update_issue_status(issue_id="lin-1", status="Done")
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_handle_issue_triggers_on_mention(self, integration):
        payload = {
            "action": "create",
            "data": {
                "id": "lin-1",
                "title": "@openswe implement feature",
                "description": "",
            },
        }
        result = await integration.handle_issue(payload)
        assert result["status"] == "processing"

    @pytest.mark.asyncio
    async def test_handle_issue_triggers_on_description_mention(self, integration):
        payload = {
            "action": "create",
            "data": {
                "id": "lin-1",
                "title": "Implement feature",
                "description": "@openswe please do this",
            },
        }
        result = await integration.handle_issue(payload)
        assert result["status"] == "processing"

    @pytest.mark.asyncio
    async def test_handle_issue_ignores_others(self, integration):
        payload = {
            "action": "create",
            "data": {
                "id": "lin-1",
                "title": "Normal issue",
                "description": "No mention",
            },
        }
        result = await integration.handle_issue(payload)
        assert result["status"] == "ignored"

    def test_empty_api_key_raises(self):
        from ai_dev_os.integrations.linear import LinearIntegration

        with pytest.raises(ValueError, match="CRITICAL SECURITY ERROR"):
            LinearIntegration(api_key="")

    def test_whitespace_api_key_raises(self):
        from ai_dev_os.integrations.linear import LinearIntegration

        with pytest.raises(ValueError, match="CRITICAL SECURITY ERROR"):
            LinearIntegration(api_key="   ")


# =============================================================================
# GitHub Integration Tests
# =============================================================================


class TestGitHubIntegration:
    @pytest.fixture
    def integration(self):
        from ai_dev_os.integrations.github import GitHubIntegration

        with patch.object(
            GitHubIntegration, "__init__", return_value=None
        ):
            integration = GitHubIntegration.__new__(GitHubIntegration)
            integration.token = "ghp_fake"
            integration.client = None
            integration.branches_created = 0
            integration.prs_created = 0
            integration.comments_added = 0
            integration.requests_failed = 0
            integration.last_error_time = None
            return integration

    @pytest.mark.asyncio
    async def test_create_branch_simulated(self, integration):
        result = await integration.create_branch(
            repo_name="test/repo", branch_name="feature/test"
        )
        assert result["status"] == "success"
        assert "simulated" in result.get("message", "")
        assert "latency" in result

    @pytest.mark.asyncio
    async def test_create_pr_simulated(self, integration):
        result = await integration.create_pr(
            repo_name="test/repo",
            branch="feature/test",
            title="Test PR",
            description="Description",
        )
        assert result["status"] == "mocked"
        assert "latency" in result

    @pytest.mark.asyncio
    async def test_add_comment_simulated(self, integration):
        result = await integration.add_comment(
            repo_name="test/repo", pr_number=42, body="Nice work!"
        )
        assert result["status"] == "success"
        assert "simulated" in result.get("message", "")
        assert "latency" in result

    @pytest.mark.asyncio
    async def test_handle_webhook_comment_triggers(self, integration):
        payload = {"comment": {"body": "@openswe run tests"}}
        result = await integration.handle_webhook_comment(payload)
        assert result["status"] == "queued"

    @pytest.mark.asyncio
    async def test_handle_webhook_comment_ignores(self, integration):
        payload = {"comment": {"body": "Just a normal comment"}}
        result = await integration.handle_webhook_comment(payload)
        assert result["status"] == "ignored"

    def test_get_metrics_initial(self, integration):
        metrics = integration.get_metrics()
        assert metrics["success_rate"] == 0.0

    def test_get_metrics_after_operations(self, integration):
        integration.branches_created = 5
        integration.prs_created = 3
        integration.comments_added = 2
        integration.requests_failed = 1

        metrics = integration.get_metrics()
        assert metrics["branches_created"] == 5
        assert metrics["success_rate"] > 0

    def test_reset_metrics(self, integration):
        integration.branches_created = 10
        integration.reset_metrics()
        assert integration.branches_created == 0
        assert integration.requests_failed == 0
