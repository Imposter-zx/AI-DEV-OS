import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SecurityManager:
    """
    Handles authentication, API key validation, and ACLs for AI Dev OS.
    """

    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {"admin": {"role": "admin", "api_keys": {}}}
        self.acls: Dict[str, List[str]] = {}  # resource_id -> list of allowed users

    def validate_api_key(self, provider: str, key: str) -> bool:
        """Strictly validate API key formats."""
        if not key:
            return False

        patterns = {
            "anthropic": r"^sk-ant-api03-[a-zA-Z0-9_-]{90,}$",
            "github": r"^(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,255}$",
            "slack": r"^xox[bpa]-[a-zA-Z0-9-]{10,}$",
            "linear": r"^lin_api_[a-zA-Z0-9]{40,}$",
        }

        pattern = patterns.get(provider.lower())
        if not pattern:
            logger.warning(f"No validation pattern for provider: {provider}")
            return True  # allow if unknown, but better to log

        return bool(re.match(pattern, key))

    def check_permission(self, user_id: str, resource_id: str, action: str = "access") -> bool:
        """Check if a user has permission for a specific resource."""
        if user_id == "admin":
            return True

        allowed_users = self.acls.get(resource_id, [])
        return user_id in allowed_users

    def grant_access(self, resource_id: str, user_id: str):
        """Grant access to a resource."""
        if resource_id not in self.acls:
            self.acls[resource_id] = []
        if user_id not in self.acls[resource_id]:
            self.acls[resource_id].append(user_id)
            logger.info(f"Granted {user_id} access to {resource_id}")

    def sanitize_logs(self, logs: List[str]) -> List[str]:
        """Remove sensitive data (API keys, etc.) from logs."""
        sanitized = []
        # Simplified regex for keys
        key_pattern = r"(sk-ant-api03-[a-zA-Z0-0_-]{10,}|ghp_[a-zA-Z0-9]{10,}|xox[bpa]-[a-zA-Z0-9-]{10,}|lin_api_[a-zA-Z0-9]{10,})"

        for log in logs:
            sanitized.append(re.sub(key_pattern, "[REDACTED]", log))
        return sanitized
