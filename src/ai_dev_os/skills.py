import json
import logging
import os
from typing import Any, Dict

try:
    from anthropic import Anthropic

    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

logger = logging.getLogger(__name__)


class BaseSkill:
    """Base class for all Skills with shared LLM client logic."""

    def __init__(self, name: str):
        self.name = name
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=api_key) if HAS_ANTHROPIC and api_key else None
        self.model = "claude-3-5-sonnet-20241022"

    def _parse_json_result(self, result_text: str) -> Dict[str, Any]:
        """Utility to parse JSON from LLM response blocks."""
        try:
            # Clean markdown blocks if present
            if result_text.startswith("```json"):
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif result_text.startswith("```"):
                result_text = result_text.split("```")[1].split("```")[0].strip()

            return json.loads(result_text)
        except (json.JSONDecodeError, IndexError):
            return {}


class DebuggingSkill(BaseSkill):
    """
    Systematic Debugging Skill for AI Dev OS.
    Analyzes error traces, instruments code with logging, and identifies root causes.
    """

    def __init__(self, name: str = "systematic-debugging"):
        super().__init__(name)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the debugging workflow:
        1. Parse error trace
        2. Identify relevant files
        3. Suggest/Apply fixes or instrumentation
        """
        error_trace = context.get("error_trace", "")
        code_context = context.get("code", "")
        logger.info(f"Starting systematic debugging for error: {error_trace[:50]}...")

        if not self.client:
            logger.warning("No ANTHROPIC_API_KEY. Falling back to basic mock debugging.")
            return {
                "status": "error",
                "analysis": "API key missing. Cannot perform dynamic analysis.",
                "suggested_fix": "Set ANTHROPIC_API_KEY",
            }

        prompt = f"Analyze this error trace and corresponding code. Identify the bug and suggest a fix.\n\nError: {error_trace}\n\nCode context: {code_context}"

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system="You are an expert Python debugger. Provide a concise JSON response with 'analysis' and 'suggested_fix' keys.",
                messages=[{"role": "user", "content": prompt}],
            )
            content_block = response.content[0]
            result_text = (
                content_block.text if hasattr(content_block, "text") else str(content_block)
            )

            parsed = self._parse_json_result(result_text)
            return {
                "status": "success",
                "analysis": parsed.get("analysis", result_text),
                "suggested_fix": parsed.get("suggested_fix", ""),
            }
        except Exception as e:
            logger.error(f"Debugging skill execution failed: {e}", exc_info=True)
            return {"status": "error", "analysis": str(e), "suggested_fix": ""}


class PerformanceOptimizationSkill(BaseSkill):
    """
    Skill for identifying and fixing performance bottlenecks.
    """

    def __init__(self, name: str = "performance-optimization"):
        super().__init__(name)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Running performance optimization analysis...")

        code_context = context.get("code", "No code provided")

        if not self.client:
            return {
                "status": "error",
                "optimizations": ["API key missing. Cannot perform dynamic analysis."],
            }

        prompt = f"Analyze this code for performance bottlenecks (memory leaks, O(n^2) loops, etc).\n\nCode: {code_context}"

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system="You are a performance engineer. Return a JSON dict with a key 'optimizations' containing a list of strings detailing how to speed up the code.",
                messages=[{"role": "user", "content": prompt}],
            )
            content_block = response.content[0]
            result_text = (
                content_block.text if hasattr(content_block, "text") else str(content_block)
            )

            parsed = self._parse_json_result(result_text)
            return {
                "status": "success",
                "optimizations": parsed.get("optimizations", [result_text]),
            }
        except Exception as e:
            logger.error(f"Performance optimization skill failed: {e}", exc_info=True)
            return {"status": "error", "optimizations": [str(e)]}


class DocumentationGenerationSkill(BaseSkill):
    """
    Skill for automatically generating and updating documentation.
    """

    def __init__(self, name: str = "doc-generation"):
        super().__init__(name)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the documentation generation workflow.
        """
        logger.info("Generating documentation updates...")

        code_context = context.get("code", "")
        file_path = context.get("file_path", "unknown.py")

        if not self.client or not code_context:
            logger.warning("No ANTHROPIC_API_KEY or no code provided.")
            return {"status": "error", "updated_files": []}

        prompt = f"Generate appropriate Python docstrings and markdown notes for this file: {file_path}\n\n{code_context}"

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system="Generate documentation. Return JSON with 'updated_files' as a list of strings representing the generated markdown layout for each documentation section.",
                messages=[{"role": "user", "content": prompt}],
            )
            content_block = response.content[0]
            result_text = (
                content_block.text if hasattr(content_block, "text") else str(content_block)
            )

            parsed = self._parse_json_result(result_text)
            updated_files = parsed.get("updated_files", [result_text])

            logger.info(
                f"Successfully generated {len(updated_files)} documentation sections for {file_path}"
            )
            return {
                "status": "success",
                "updated_files": updated_files,
            }
        except Exception as e:
            logger.error(f"Documentation generation skill failed: {e}", exc_info=True)
            return {"status": "error", "updated_files": [str(e)]}
