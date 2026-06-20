"""
AI Dev OS - Main Orchestration Engine

Coordinates Deep Agents, Superpowers skills, sandboxes, training, simulation, and HUD.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ai_dev_os.sandbox import SandboxProvider
from ai_dev_os.utils.context import ContextManager
from ai_dev_os.utils.error_handling import with_retry
from ai_dev_os.utils.snapshot import SnapshotManager

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class WorkflowPhase(Enum):
    """Stages of the AI Dev OS workflow."""

    BRAINSTORMING = "brainstorming"
    PLANNING = "planning"
    EXECUTION = "execution"
    VALIDATION = "validation"
    MERGE = "merge"


class BaseLLM(ABC):
    @abstractmethod
    def generate(
        self,
        system: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float = 0.7,
    ) -> Tuple[str, int, int]:
        pass


class AnthropicLLM(BaseLLM):
    def __init__(self):
        import os

        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is missing.")
        self.client = Anthropic(api_key=api_key)

    def generate(
        self,
        system: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float = 0.7,
    ) -> Tuple[str, int, int]:
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
        )
        return (
            response.content[0].text,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )


class LocalLLM(BaseLLM):
    def __init__(self, model_path: str):
        try:
            from llama_cpp import Llama

            self.model = Llama(model_path=model_path, n_ctx=8192, verbose=False)
        except ImportError:
            raise RuntimeError("llama-cpp-python is required for LocalLLM")

    def generate(
        self,
        system: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float = 0.7,
    ) -> Tuple[str, int, int]:
        prompt = f"<system>\n{system}\n</system>\n"
        for m in messages:
            prompt += f"<{m['role']}>\n{m['content']}\n</{m['role']}>\n"
        prompt += "<assistant>\n"

        response = self.model(prompt, max_tokens=max_tokens, temperature=temperature)
        text = response["choices"][0]["text"]
        return text, len(prompt) // 4, len(text) // 4


@dataclass
class AgentConfig:
    """Configuration for a subagent."""

    name: str
    role: str  # "code", "training", "simulation"
    sandbox_provider: SandboxProvider
    max_tokens: int = 50000
    temperature: float = 0.7
    tools: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.tools:
            self.tools = self._default_tools()

    def _default_tools(self) -> List[str]:
        """Return default tools based on role."""
        defaults = {
            "code": ["read_file", "write_file", "execute", "git_commit", "github_pr"],
            "training": ["unsloth_train", "bitnet_quantize", "model_upload"],
            "simulation": ["newton_sim", "plot_results", "upload_metrics"],
        }
        return defaults.get(self.role, [])


@dataclass
class WorkflowState:
    """Complete state of a workflow execution."""

    id: str
    phase: WorkflowPhase
    user_request: str
    design_doc: Optional[str] = None
    implementation_plan: Optional[str] = None
    subagent_configs: List[AgentConfig] = field(default_factory=list)
    execution_results: Dict[str, Any] = field(default_factory=dict)
    context_usage: float = 0.0  # percentage
    active_agents: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def add_log(self, message: str):
        """Add a log entry."""
        self.logs.append(f"[{datetime.now(timezone.utc).isoformat()}] {message}")
        logger.info(message)


class SuperpowerSkill:
    """Wrapper for Superpowers skills."""

    def __init__(
        self,
        name: str,
        trigger: str,
        system_prompt: str,
        context_manager: Optional[ContextManager] = None,
        llm_provider: Optional[BaseLLM] = None,
    ):
        self.name = name
        self.trigger = trigger
        self.system_prompt = system_prompt
        self.context_manager = context_manager or ContextManager()
        self.llm = llm_provider or AnthropicLLM()

    @with_retry(max_retries=3)
    async def execute(self, state: WorkflowState) -> str:
        """Execute the skill against the current state with caching."""
        prompt = f"""
{self.system_prompt}

Current request: {state.user_request}

Previous context:
- Phase: {state.phase.value}
- Design doc: {state.design_doc or "None yet"}
- Plan: {state.implementation_plan or "None yet"}

Generate output for this skill:
"""

        # Caching optimization
        import hashlib
        import json

        cache_dir = Path.home() / ".ai-dev-os" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        prompt_hash = hashlib.md5(
            prompt.encode("utf-8")
        ).hexdigest()  # nosec B324 - used for caching, not security
        cache_file = cache_dir / f"{self.name}_{prompt_hash}.json"

        if cache_file.exists():
            state.add_log(f"Cache hit for skill optimization: {self.name}")
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    return data.get("result", "")
            except json.JSONDecodeError:
                pass  # Fall back to generation if cache is corrupted

        state.add_log(f"Executing skill: {self.name}")

        # Track input tokens
        in_tokens = self.context_manager.count_tokens(prompt) + self.context_manager.count_tokens(
            self.system_prompt
        )

        # Execute via agnostic LLM provider
        result, in_t, out_t = self.llm.generate(
            system=self.system_prompt,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )

        in_tokens += in_t
        out_tokens = out_t

        # Track usage in context manager
        self.context_manager.track_usage(state.id, self.name, in_tokens + out_tokens)

        # Update state percentage (assuming 200k limit for Claude 3.5 Sonnet)
        state.context_usage = self.context_manager.get_usage_percentage(state.id, 200000)

        # Save cache
        with open(cache_file, "w") as f:
            json.dump({"result": result}, f)

        state.add_log(f"Skill {self.name} completed, tokens: {in_tokens} in / {out_tokens} out")

        return result


class ClaudeHUDIntegration:
    """Real-time Claude HUD status updates."""

    def __init__(self):
        self.status_file = Path.home() / ".ai-dev-os" / "hud_status.json"
        self.status_file.parent.mkdir(parents=True, exist_ok=True)

    def update(self, state: WorkflowState, context_usage: float, active_agents: List[str]):
        """Update HUD with current state."""
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": state.phase.value,
            "context_usage": f"{context_usage:.1f}%",
            "active_agents": active_agents,
            "recent_logs": state.logs[-3:] if state.logs else [],
        }

        with open(self.status_file, "w") as f:
            json.dump(status, f, indent=2)

        # Format for terminal display
        agent_str = ", ".join(active_agents) if active_agents else "none"
        print(
            f"\n[HUD] Phase: {state.phase.value} | Context: {context_usage:.1f}% | Agents: {agent_str}"
        )


class SubagentOrchestrator:
    """Orchestrates parallel subagent execution."""

    def __init__(
        self,
        sandbox_provider: SandboxProvider = SandboxProvider.MODAL,
        context_manager: Optional[ContextManager] = None,
        llm_provider: Optional[BaseLLM] = None,
    ):
        self.sandbox_provider = sandbox_provider
        self.context_manager = context_manager or ContextManager()
        self.llm = llm_provider or AnthropicLLM()
        self.hud = ClaudeHUDIntegration()

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Bind strings to actual python executions."""
        try:
            if tool_name == "read_file":
                with open(args["path"], "r", encoding="utf-8") as f:
                    return f.read()
            elif tool_name == "write_file":
                import os

                os.makedirs(os.path.dirname(args["path"]), exist_ok=True)
                with open(args["path"], "w", encoding="utf-8") as f:
                    f.write(args["content"])
                return f"Successfully wrote to {args['path']}"
            elif tool_name == "execute":
                import subprocess

                res = subprocess.run(
                    args["command"], shell=True, capture_output=True, text=True
                )  # nosec B602 - intentional tool feature
                return f"Exit: {res.returncode}\nOut: {res.stdout}\nErr: {res.stderr}"
            else:
                return f"Tool {tool_name} not implemented."
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    @with_retry(max_retries=3)
    async def spawn_agent(self, config: AgentConfig, task_description: str) -> str:
        """Spawn a subagent to handle a specific task with tool use."""

        tools_str = "\n".join([f"- {tool}" for tool in config.tools])

        system_prompt = f"""
You are a specialized {config.role} agent in an autonomous development system.

Role: {config.role}
Sandbox: {self.sandbox_provider.value}
Available tools:
{tools_str}

Guidelines:
1. Execute your task methodically
2. Log all important steps
3. Validate results before reporting
4. Handle errors gracefully
5. Provide clear output for downstream tasks

To use a tool, you must output a JSON block like this exactly once per message:
```json
{{"tool": "execute", "args": {{"command": "echo 'hello'"}}}}
```
I will run the tool and supply the output. You may use tools continuously until you are finished. Then provide your final answer without a tool block.

Task:
{task_description}
"""

        messages = [{"role": "user", "content": "Begin execution."}]
        total_in, total_out = 0, 0
        final_result = ""

        import json
        import re

        for step in range(5):  # Max iterations
            text, in_t, out_t = self.llm.generate(
                system=system_prompt,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )
            total_in += in_t
            total_out += out_t

            match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                try:
                    tool_call = json.loads(match.group(1))
                    tool_name = tool_call.get("tool")
                    args = tool_call.get("args", {})

                    logger.info(f"Agent {config.name} executing tool: {tool_name}")
                    tool_result = self._execute_tool(tool_name, args)

                    messages.append({"role": "assistant", "content": text})
                    messages.append(
                        {
                            "role": "user",
                            "content": f"Tool result:\n{tool_result}\nContinue execution.",
                        }
                    )
                except json.JSONDecodeError:
                    messages.append({"role": "assistant", "content": text})
                    messages.append(
                        {
                            "role": "user",
                            "content": "Failed to parse JSON. Please format correctly.",
                        }
                    )
            else:
                final_result = text
                break

        if not final_result:
            final_result = text

        # Track usage
        self.context_manager.track_usage("workflow-dummy", config.name, total_in + total_out)

        logger.info(f"Subagent {config.name} completed, tokens: {total_in} in / {total_out} out")

        return final_result

    async def orchestrate(self, state: WorkflowState) -> WorkflowState:
        """Orchestrate all subagents in parallel."""

        state.add_log(f"Starting parallel execution of {len(state.subagent_configs)} agents")
        state.phase = WorkflowPhase.EXECUTION

        # Update HUD
        agent_names = [cfg.name for cfg in state.subagent_configs]
        self.hud.update(state, state.context_usage, agent_names)

        # Execute all agents in parallel
        tasks = []
        for config in state.subagent_configs:
            task_desc = self._generate_task_description(state, config)
            task = self.spawn_agent(config, task_desc)
            tasks.append((config.name, task))

        # Gather results
        results = {}
        for agent_name, task in tasks:
            try:
                result = await task
                results[agent_name] = result
                state.add_log(f"Agent {agent_name} completed successfully")
            except Exception as e:
                state.add_log(f"Agent {agent_name} failed: {str(e)}")
                results[agent_name] = f"ERROR: {str(e)}"

        state.execution_results = results
        state.add_log("Parallel execution completed")

        # Update HUD
        self.hud.update(state, state.context_usage, [])

        return state

    def _generate_task_description(self, state: WorkflowState, config: AgentConfig) -> str:
        """Generate specific task description for an agent."""

        task_descriptions = {
            "code": f"""
Implement the following plan:
{state.implementation_plan}

Requirements:
- Write clean, well-documented code
- Follow TDD: write tests first
- Commit meaningful changes
- Create a draft PR when complete
""",
            "training": f"""
Fine-tune a model with these specifications:
{state.implementation_plan}

Requirements:
- Use Unsloth for 2x speed, 70% less VRAM
- Monitor training loss and validate
- Quantize to BitNet format when complete
- Save checkpoint and report metrics
""",
            "simulation": f"""
Run simulations for:
{state.implementation_plan}

Requirements:
- Use Newton for GPU-accelerated physics
- Run episodes in parallel
- Measure success rate and stability
- Generate plots and metrics
- Report results for validation
""",
        }

        return task_descriptions.get(
            config.role, "Execute this task: " + (state.implementation_plan or "")
        )


class AIDevOSOrchestrator:
    """Main orchestrator for the entire AI Dev OS system."""

    def __init__(
        self,
        sandbox_provider: SandboxProvider = SandboxProvider.MODAL,
        llm_provider: Optional[BaseLLM] = None,
    ):
        self.sandbox_provider = sandbox_provider
        self.llm = llm_provider or AnthropicLLM()
        self.hud = ClaudeHUDIntegration()

        # Context manager
        self.context_manager = ContextManager()

        # Initialize Snapshot manager
        self.snapshot_manager = SnapshotManager()

        # Initialize Superpowers skills
        self.skills = self._load_skills()

        # Subagent orchestrator
        self.subagent_orchestrator = SubagentOrchestrator(
            sandbox_provider, self.context_manager, self.llm
        )

        # Load AGENTS.md rules
        self.agents_rules = self._load_agents_rules()

    def _load_skills(self) -> Dict[str, SuperpowerSkill]:
        """Load Superpowers skills."""
        return {
            "brainstorming": SuperpowerSkill(
                name="brainstorming",
                trigger="Before any implementation",
                system_prompt="""
You are a brainstorming expert. Help refine the user's idea through Socratic questioning.
Ask clarifying questions, explore alternatives, and present the design in digestible chunks.
Output: A clear design document with requirements, architecture, and acceptance criteria.
""",
                context_manager=self.context_manager,
            ),
            "planning": SuperpowerSkill(
                name="planning",
                trigger="After design approval",
                system_prompt="""
You are a project planning expert. Break the design into bite-sized tasks (2-5 min each).
Each task must include: exact file paths, complete code snippets, and verification steps.
Output: A detailed implementation plan with task list and dependencies.
""",
                context_manager=self.context_manager,
            ),
            "code-review": SuperpowerSkill(
                name="code-review",
                trigger="Before merge",
                system_prompt="""
You are a code reviewer. Check the implementation against the plan.
Report issues by severity: critical (blocks merge), major (should fix), minor (nice to have).
Output: Review report with issues and recommendations.
""",
                context_manager=self.context_manager,
            ),
            "research": SuperpowerSkill(
                name="research",
                trigger="Discovery",
                system_prompt="""
You are a research expert. Search the codebase for patterns, anti-patterns, and architectural constraints.
Output: A research report with findings and cross-references to relevant files.
""",
                context_manager=self.context_manager,
            ),
            "security-audit": SuperpowerSkill(
                name="security-audit",
                trigger="Safety Check",
                system_prompt="""
You are a security professional. Scan the codebase for leaked secrets, insecure dependencies, and common vulnerabilities.
Output: A list of security findings with severity and remediation steps.
""",
                context_manager=self.context_manager,
            ),
            "performance-optimization": SuperpowerSkill(
                name="performance-optimization",
                trigger="Efficiency",
                system_prompt="""
You are a performance engineer. Profile the system to find bottlenecks, memory leaks, and slow database queries.
Output: A performance report with specific optimization recommendations.
""",
                context_manager=self.context_manager,
            ),
        }

    def _load_agents_rules(self) -> Dict[str, Any]:
        """Load AGENTS.md rules from repo."""
        agents_md = Path.cwd() / "AGENTS.md"

        if not agents_md.exists():
            logger.warning("AGENTS.md not found, using defaults")
            return {}

        # Parse AGENTS.md (simplified - in production use proper markdown parser)
        content = agents_md.read_text()

        rules = {
            "raw": content,
            "enforce_brainstorming": "brainstorming: REQUIRED" in content,
            "enforce_planning": "writing-plans: REQUIRED" in content,
            "enforce_tdd": "test-driven-development: REQUIRED" in content,
            "enforce_review": "requesting-code-review: REQUIRED" in content,
        }

        return rules

    async def run(self, user_request: str) -> WorkflowState:
        """Main entry point: run a complete workflow."""

        # Initialize workflow state
        import uuid

        state = WorkflowState(
            id=str(uuid.uuid4()),
            phase=WorkflowPhase.BRAINSTORMING,
            user_request=user_request,
        )

        state.add_log(f"Starting workflow for request: {user_request}")
        self.hud.update(state, state.context_usage, [])
        self._save_snapshot(state)

        # Phase 1: Brainstorming
        logger.info("=" * 60)
        logger.info("PHASE 1: BRAINSTORMING")
        logger.info("=" * 60)

        design_doc = await self.skills["brainstorming"].execute(state)
        state.design_doc = design_doc
        state.add_log("Design doc generated")
        self._save_snapshot(state)

        print("\n📋 DESIGN DOCUMENT:\n")
        print(design_doc)
        print("\n" + "=" * 60)

        # Ask for approval
        user_approval = input("\nApprove design? (yes/no): ").lower().strip()
        if user_approval != "yes":
            state.add_log("Design rejected by user")
            return state

        state.add_log("Design approved by user")

        # Phase 2: Planning
        logger.info("=" * 60)
        logger.info("PHASE 2: PLANNING")
        logger.info("=" * 60)

        state.phase = WorkflowPhase.PLANNING
        self._save_snapshot(state)
        plan = await self.skills["planning"].execute(state)
        state.implementation_plan = plan
        state.add_log("Implementation plan generated")
        self._save_snapshot(state)

        print("\n📝 IMPLEMENTATION PLAN:\n")
        print(plan)
        print("\n" + "=" * 60)

        # Phase 4: Execution (Subagents)
        logger.info("=" * 60)
        logger.info("PHASE 4: EXECUTION (Subagents)")
        logger.info("=" * 60)

        # Determine which agents we need
        state.subagent_configs = self._determine_agents(user_request)

        state = await self.subagent_orchestrator.orchestrate(state)
        self._save_snapshot(state)

        # Phase 5: Validation & Code Review
        logger.info("=" * 60)
        logger.info("PHASE 5: VALIDATION & CODE REVIEW")
        logger.info("=" * 60)

        state.phase = WorkflowPhase.VALIDATION
        review = await self.skills["code-review"].execute(state)
        state.add_log("Code review completed")
        self._save_snapshot(state)

        print("\n✅ CODE REVIEW:\n")
        print(review)

        # Phase 6: Merge
        logger.info("=" * 60)
        logger.info("PHASE 6: MERGE")
        logger.info("=" * 60)

        state.phase = WorkflowPhase.MERGE
        state.add_log("Workflow completed successfully")
        self._save_snapshot(state)

        print("\n🎉 Workflow completed! PR ready for review.")

        return state

    def _save_snapshot(self, state: WorkflowState):
        """Helper to save a state snapshot."""
        try:
            # Convert dataclass to dict (simplified)
            state_dict = {
                "id": state.id,
                "phase": state.phase.value,
                "user_request": state.user_request,
                "design_doc": state.design_doc,
                "implementation_plan": state.implementation_plan,
                "execution_results": state.execution_results,
                "created_at": state.created_at,
                "logs": state.logs,
            }
            self.snapshot_manager.save_snapshot(state.id, state.phase.value, state_dict)
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")

    def _determine_agents(self, user_request: str) -> List[AgentConfig]:
        """Determine which agents are needed for this request."""

        request_lower = user_request.lower()
        agents = []

        # Heuristic: detect what kind of task this is
        if any(word in request_lower for word in ["code", "build", "feature", "fix", "test"]):
            agents.append(
                AgentConfig(
                    name="code-agent",
                    role="code",
                    sandbox_provider=self.sandbox_provider,
                )
            )

        if any(word in request_lower for word in ["train", "finetune", "model", "lora"]):
            agents.append(
                AgentConfig(
                    name="training-agent",
                    role="training",
                    sandbox_provider=self.sandbox_provider,
                )
            )

        if any(word in request_lower for word in ["simul", "robot", "physic", "test"]):
            agents.append(
                AgentConfig(
                    name="simulation-agent",
                    role="simulation",
                    sandbox_provider=self.sandbox_provider,
                )
            )

        # Default to code agent if unclear
        if not agents:
            agents.append(
                AgentConfig(
                    name="code-agent",
                    role="code",
                    sandbox_provider=self.sandbox_provider,
                )
            )

        return agents


async def main():
    """Example main function."""

    orchestrator = AIDevOSOrchestrator(sandbox_provider=SandboxProvider.MODAL)

    # Example request
    user_request = "Build a simple authentication module with tests and documentation"

    state = await orchestrator.run(user_request)

    # Print summary
    print("\n" + "=" * 60)
    print("WORKFLOW SUMMARY")
    print("=" * 60)
    print(f"Workflow ID: {state.id}")
    print(f"Status: {'COMPLETED' if state.phase == WorkflowPhase.MERGE else 'IN PROGRESS'}")
    print(f"Total logs: {len(state.logs)}")
    print(f"Agents used: {len(state.subagent_configs)}")

    # Save state for reference
    state_file = Path.home() / ".ai-dev-os" / f"workflow_{state.id}.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    with open(state_file, "w") as f:
        # Convert dataclasses to dicts for JSON serialization
        state_dict = {
            "id": state.id,
            "phase": state.phase.value,
            "user_request": state.user_request,
            "design_doc": state.design_doc,
            "implementation_plan": state.implementation_plan,
            "execution_results": state.execution_results,
            "created_at": state.created_at,
            "logs": state.logs,
        }
        json.dump(state_dict, f, indent=2)

    print(f"\nWorkflow state saved to: {state_file}")


if __name__ == "__main__":
    asyncio.run(main())
