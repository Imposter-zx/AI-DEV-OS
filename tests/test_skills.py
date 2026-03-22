import pytest

from ai_dev_os.skills import (
    DebuggingSkill,
    DocumentationGenerationSkill,
    PerformanceOptimizationSkill,
)


@pytest.mark.asyncio
async def test_debugging_skill():
    skill = DebuggingSkill()
    result = await skill.execute({"error_trace": "ValueError: something went wrong"})
    assert result["status"] == "success"
    assert "analysis" in result


@pytest.mark.asyncio
async def test_performance_skill():
    skill = PerformanceOptimizationSkill()
    result = await skill.execute({})
    assert result["status"] == "success"
    assert len(result["optimizations"]) > 0


@pytest.mark.asyncio
async def test_doc_skill():
    skill = DocumentationGenerationSkill()
    result = await skill.execute({})
    assert result["status"] == "success"
    assert "updated_files" in result
