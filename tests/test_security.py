import pytest

from ai_dev_os.utils.security import SecurityManager


@pytest.fixture
def security_manager():
    return SecurityManager()


def test_validate_api_key_anthropic(security_manager):
    valid_key = "sk-ant-api03-" + "a" * 90
    assert security_manager.validate_api_key("anthropic", valid_key) is True
    assert security_manager.validate_api_key("anthropic", "invalid") is False


def test_validate_api_key_github(security_manager):
    valid_key = "ghp_abcdefghijklmnopqrstuvwxyz01234567891234"
    assert security_manager.validate_api_key("github", valid_key) is True
    assert security_manager.validate_api_key("github", "gho_invalid") is False


def test_check_permission(security_manager):
    security_manager.grant_access("sandbox-1", "user-1")
    assert security_manager.check_permission("user-1", "sandbox-1") is True
    assert security_manager.check_permission("user-2", "sandbox-1") is False
    assert security_manager.check_permission("admin", "sandbox-1") is True


def test_sanitize_logs(security_manager):
    logs = ["Connected with ghp_1234567890abcdef", "User logged in"]
    sanitized = security_manager.sanitize_logs(logs)
    assert "ghp_" not in sanitized[0]
    assert "[REDACTED]" in sanitized[0]
