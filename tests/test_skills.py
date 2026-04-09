import pytest

from ai_dev_os.skills import (
    DebuggingSkill,
    DocumentationGenerationSkill,
    PerformanceOptimizationSkill,
)
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")



@pytest.mark.asyncio
async def test_debugging_skill():
    skill = DebuggingSkill()
    result = await skill.execute({"error_trace": "ValueError: something went wrong"})
    # Since we lack an API key locally or in CI, it falls back to a graceful error
    assert result["status"] == "error"
    assert "analysis" in result


@pytest.mark.asyncio
async def test_performance_skill():
    skill = PerformanceOptimizationSkill()
    result = await skill.execute({})
    assert result["status"] == "error"
    assert len(result["optimizations"]) > 0


@pytest.mark.asyncio
async def test_doc_skill():
    skill = DocumentationGenerationSkill()
    result = await skill.execute({})
    assert result["status"] == "error"
    assert "updated_files" in result
