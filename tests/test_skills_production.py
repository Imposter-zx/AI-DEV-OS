import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set a dummy API key to avoid initialization errors that might bypass mocks
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-api03-template-key-for-tests-only"

from ai_dev_os.skills import (
    DebuggingSkill,
    DocumentationGenerationSkill,
    PerformanceOptimizationSkill,
)


@pytest.mark.asyncio
async def test_debugging_skill_uses_correct_model():
    with patch("ai_dev_os.skills.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create = MagicMock()

        skill = DebuggingSkill()
        # Mock successful JSON response
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '{"analysis": "test bug", "suggested_fix": "test fix"}'
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        await skill.execute({"error_trace": "test", "code": "test"})

        # Verify model version
        _, kwargs = mock_client.messages.create.call_args
        assert kwargs["model"] == "claude-3-5-sonnet-20241022"


@pytest.mark.asyncio
async def test_doc_generation_skill_returns_content():
    with patch("ai_dev_os.skills.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create = MagicMock()

        skill = DocumentationGenerationSkill()
        # Mock successful JSON response
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '{"updated_files": ["# Documentation\\nTest content"]}'
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        result = await skill.execute({"file_path": "test.py", "code": "print('hello')"})

        assert result["status"] == "success"
        assert "# Documentation" in result["updated_files"][0]
        assert "Test content" in result["updated_files"][0]


@pytest.mark.asyncio
async def test_skills_handle_api_errors_gracefully():
    with patch("ai_dev_os.skills.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create = MagicMock(side_effect=Exception("API Error"))

        skill = PerformanceOptimizationSkill()
        result = await skill.execute({"code": "test"})

        assert result["status"] == "error"
        assert "API Error" in str(result["optimizations"])
