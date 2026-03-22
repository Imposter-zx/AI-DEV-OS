"""
Comprehensive tests for core.py - AIDevOSOrchestrator and related classes.
"""

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

try:
    from unittest.mock import AsyncMock
except ImportError:

    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)


from ai_dev_os.core import (
    AgentConfig,
    AIDevOSOrchestrator,
    ClaudeHUDIntegration,
    SandboxProvider,
    SubagentOrchestrator,
    SuperpowerSkill,
    WorkflowPhase,
    WorkflowState,
)

# ─── Workflow State Tests ───────────────────────────────────────


class TestWorkflowState:
    def test_state_initialization(self):
        state = WorkflowState(
            id="test-1", phase=WorkflowPhase.BRAINSTORMING, user_request="Build auth module"
        )
        assert state.id == "test-1"
        assert state.phase == WorkflowPhase.BRAINSTORMING
        assert state.user_request == "Build auth module"
        assert state.design_doc is None
        assert state.implementation_plan is None
        assert state.subagent_configs == []
        assert state.execution_results == {}
        assert state.active_agents == []
        assert state.logs == []
        assert state.created_at is not None

    def test_add_log(self):
        state = WorkflowState(id="test-2", phase=WorkflowPhase.PLANNING, user_request="test")
        state.add_log("First log")
        state.add_log("Second log")
        assert len(state.logs) == 2
        assert "First log" in state.logs[0]
        assert "Second log" in state.logs[1]

    def test_state_transitions(self):
        state = WorkflowState(id="test-3", phase=WorkflowPhase.BRAINSTORMING, user_request="test")
        assert state.phase == WorkflowPhase.BRAINSTORMING

        state.phase = WorkflowPhase.PLANNING
        assert state.phase == WorkflowPhase.PLANNING

        state.phase = WorkflowPhase.EXECUTION
        assert state.phase == WorkflowPhase.EXECUTION

        state.phase = WorkflowPhase.VALIDATION
        assert state.phase == WorkflowPhase.VALIDATION

        state.phase = WorkflowPhase.MERGE
        assert state.phase == WorkflowPhase.MERGE

    def test_context_usage(self):
        state = WorkflowState(id="test-4", phase=WorkflowPhase.EXECUTION, user_request="test")
        state.context_usage = 0.0
        assert state.context_usage == 0.0

        state.context_usage = 75.0
        assert state.context_usage == 75.0

        state.context_usage = 90.0
        assert state.context_usage == 90.0


# ─── Agent Config Tests ─────────────────────────────────────────


class TestAgentConfig:
    def test_code_agent_defaults(self):
        agent = AgentConfig(name="code-agent", role="code", sandbox_provider=SandboxProvider.DOCKER)
        assert "read_file" in agent.tools
        assert "write_file" in agent.tools
        assert "execute" in agent.tools
        assert "git_commit" in agent.tools
        assert "github_pr" in agent.tools

    def test_training_agent_defaults(self):
        agent = AgentConfig(
            name="training-agent", role="training", sandbox_provider=SandboxProvider.MODAL
        )
        assert "unsloth_train" in agent.tools
        assert "bitnet_quantize" in agent.tools
        assert "model_upload" in agent.tools

    def test_simulation_agent_defaults(self):
        agent = AgentConfig(
            name="sim-agent", role="simulation", sandbox_provider=SandboxProvider.MODAL
        )
        assert "newton_sim" in agent.tools
        assert "plot_results" in agent.tools
        assert "upload_metrics" in agent.tools

    def test_unknown_role_empty_tools(self):
        agent = AgentConfig(
            name="unknown-agent", role="unknown", sandbox_provider=SandboxProvider.DOCKER
        )
        assert agent.tools == []

    def test_custom_max_tokens(self):
        agent = AgentConfig(
            name="test", role="code", sandbox_provider=SandboxProvider.DOCKER, max_tokens=100000
        )
        assert agent.max_tokens == 100000

    def test_custom_temperature(self):
        agent = AgentConfig(
            name="test", role="code", sandbox_provider=SandboxProvider.DOCKER, temperature=0.3
        )
        assert agent.temperature == 0.3


# ─── Orchestrator Tests ──────────────────────────────────────────


class TestAIDevOSOrchestrator:
    @patch("ai_dev_os.core.Anthropic")
    def test_initialization(self, mock_anthropic):
        orchestrator = AIDevOSOrchestrator(sandbox_provider=SandboxProvider.DOCKER)
        assert orchestrator.sandbox_provider == SandboxProvider.DOCKER
        assert "brainstorming" in orchestrator.skills
        assert "planning" in orchestrator.skills
        assert "code-review" in orchestrator.skills

    @patch("ai_dev_os.core.Anthropic")
    def test_determine_agents_code(self, mock_anthropic):
        orchestrator = AIDevOSOrchestrator()
        agents = orchestrator._determine_agents("Build a new feature for auth")
        roles = [a.role for a in agents]
        assert "code" in roles

    @patch("ai_dev_os.core.Anthropic")
    def test_determine_agents_training(self, mock_anthropic):
        orchestrator = AIDevOSOrchestrator()
        agents = orchestrator._determine_agents("Train a model on my dataset")
        roles = [a.role for a in agents]
        assert "training" in roles

    @patch("ai_dev_os.core.Anthropic")
    def test_determine_agents_simulation(self, mock_anthropic):
        orchestrator = AIDevOSOrchestrator()
        agents = orchestrator._determine_agents("Run a robot simulation")
        roles = [a.role for a in agents]
        assert "simulation" in roles

    @patch("ai_dev_os.core.Anthropic")
    def test_determine_agents_default(self, mock_anthropic):
        orchestrator = AIDevOSOrchestrator()
        agents = orchestrator._determine_agents("Something vague")
        assert len(agents) == 1
        assert agents[0].role == "code"

    @patch("ai_dev_os.core.Anthropic")
    def test_determine_agents_multi_role(self, mock_anthropic):
        orchestrator = AIDevOSOrchestrator()
        agents = orchestrator._determine_agents("Build code and train a model")
        roles = [a.role for a in agents]
        assert "code" in roles
        assert "training" in roles

    @patch("ai_dev_os.core.Anthropic")
    def test_skills_loaded(self, mock_anthropic):
        orchestrator = AIDevOSOrchestrator()
        assert len(orchestrator.skills) == 3
        for name, skill in orchestrator.skills.items():
            assert isinstance(skill, SuperpowerSkill)
            assert skill.name == name


# ─── HUD Integration Tests ──────────────────────────────────────


class TestClaudeHUDIntegration:
    def test_hud_update_creates_file(self):
        hud = ClaudeHUDIntegration()
        state = WorkflowState(
            id="hud-test", phase=WorkflowPhase.EXECUTION, user_request="test request"
        )
        state.context_usage = 42.5

        hud.update(state, 42.5, ["agent-1", "agent-2"])

        assert hud.status_file.exists()
        with open(hud.status_file) as f:
            data = json.load(f)
        assert data["phase"] == "execution"
        assert data["context_usage"] == "42.5%"
        assert "agent-1" in data["active_agents"]
        assert "agent-2" in data["active_agents"]

    def test_hud_update_empty_agents(self):
        hud = ClaudeHUDIntegration()
        state = WorkflowState(id="hud-test-2", phase=WorkflowPhase.MERGE, user_request="test")
        hud.update(state, 0.0, [])

        with open(hud.status_file) as f:
            data = json.load(f)
        assert data["active_agents"] == []


# ─── Sandbox Provider Tests ─────────────────────────────────────


class TestSandboxProvider:
    def test_all_providers(self):
        assert SandboxProvider.MODAL.value == "modal"
        assert SandboxProvider.DAYTONA.value == "daytona"
        assert SandboxProvider.RUNLOOP.value == "runloop"
        assert SandboxProvider.DOCKER.value == "docker"


# ─── Workflow Phase Tests ────────────────────────────────────────


class TestWorkflowPhase:
    def test_all_phases(self):
        assert WorkflowPhase.BRAINSTORMING.value == "brainstorming"
        assert WorkflowPhase.PLANNING.value == "planning"
        assert WorkflowPhase.EXECUTION.value == "execution"
        assert WorkflowPhase.VALIDATION.value == "validation"
        assert WorkflowPhase.MERGE.value == "merge"
