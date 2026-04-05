# AI Dev OS - Unified AI Development Platform

**A complete software development workflow for autonomous AI agents** combining Deep Agents orchestration, Superpowers skills enforcement, Newton physics simulation, Unsloth model training, BitNet inference, and real-time Claude HUD observability.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Built on LangGraph](https://img.shields.io/badge/built%20on-LangGraph-orange)](https://langchain-ai.github.io/langgraph/)

## 🎯 What is AI Dev OS?

AI Dev OS is an integrated platform where autonomous AI agents can handle complete engineering workflows—from design through deployment—with human oversight at key checkpoints. It's built on the same architecture used by leading orgs like Stripe, Ramp, and Coinbase for internal coding agents.

**Key components:**
- 🤖 **Open SWE** - Agent orchestration with sandboxed execution
- 🧠 **Superpowers** - Mandatory workflow enforcement (brainstorming → planning → TDD → review)
- 🎓 **Unsloth** - Fast model training (2x speedup, 70% less VRAM)
- ⚙️ **Newton** - GPU-accelerated physics simulation for robotics
- ⚡ **BitNet.cpp** - Efficient 1-bit LLM inference on CPU/GPU
- 📊 **Claude HUD** - Real-time observability of context, tools, agents, and progress

## 🏗️ Visual Architecture

I have integrated the official **Unified AI Platform Architecture** from your design board into the project documentation.

```
Developer Request (Slack/Linear/CLI)
     ↓
     └─→ Open SWE Harness (Deep Agents + Middleware)
         ├─→ Superpowers:brainstorming (Design refinement)
         ├─→ Superpowers:using-git-worktrees (Isolated branch)
         ├─→ Superpowers:writing-plans (Task breakdown)
         └─→ Subagent Orchestration
             ├─→ Agent-A (Sandbox-1): Code + Testing
             ├─→ Agent-B (Sandbox-2): Training (Unsloth)
             └─→ Agent-C (Sandbox-3): Simulation (Newton)
                     ↓
             Real-time Feedback (Claude HUD)
                     ↓
             Superpowers:verification + Code Review
                     ↓
             Auto-PR + Merge to Production
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for Claude Code)
- Docker (recommended for sandboxes)
- NVIDIA GPU (for Newton + Unsloth training, optional for inference)

### Installation

#### 1. Clone and Setup
```bash
git clone https://github.com/Imposter-zx/ai-dev-os.git
cd ai-dev-os
```

#### 2. Install Dependencies (Powered by `uv`)
```bash
# We use uv for lightning-fast dependency management
uv sync --all-groups
```

#### 3. Initialize Sandboxes (Modal, Daytona, or Runloop)
```bash
python scripts/setup-sandboxes.py --provider modal
# or
python scripts/setup-sandboxes.py --provider daytona
```

#### 4. Configure Claude Code & Plugins
```bash
# In Claude Code, run:
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
/plugin install claude-hud
/claude-hud:setup
```

#### 5. Set Up AGENTS.md (Repo Conventions)
```bash
cp templates/AGENTS.md.template ./AGENTS.md
# Edit AGENTS.md with your repo's conventions
```

#### 6. Start AI Dev OS
```bash
python -m ai_dev_os start --mode development
```

## 📋 Project Structure

```
ai-dev-os/
├── README.md                          # This file
├── AGENTS.md                          # Repo conventions for agents
├── requirements.txt                   # Core dependencies
├── requirements-dev.txt               # Development tools
├── pyproject.toml                     # Project metadata
├── .github/
│   └── workflows/
│       └── agent-validation.yml       # CI/CD for agent runs
├── src/
│   ├── ai_dev_os/
│   │   ├── __init__.py
│   │   ├── core.py                    # Main orchestration engine
│   │   ├── agents.py                  # Deep Agents wrapper
│   │   ├── sandbox.py                 # Sandbox abstraction
│   │   ├── skills.py                  # Superpowers skill loader
│   │   ├── hud.py                     # Claude HUD integration
│   │   ├── models.py                  # Training + inference (Unsloth + BitNet)
│   │   └── simulation.py              # Newton integration
│   ├── integrations/
│   │   ├── slack.py                   # Slack bot
│   │   ├── linear.py                  # Linear issue integration
│   │   └── github.py                  # GitHub PR automation
│   └── utils/
│       ├── context.py                 # Context window management
│       └── logger.py                  # Structured logging
├── scripts/
│   ├── setup-sandboxes.py             # Sandbox initialization
│   ├── create-skill.py                # Skill generation helper
│   ├── run-benchmark.py               # Performance benchmarking
│   └── migrate-to-bitnet.py           # Model quantization
├── templates/
│   ├── AGENTS.md.template             # Agent rules template
│   ├── skill-template/                # Superpowers skill scaffold
│   └── example-project/               # Complete example (robot walker)
├── tests/
│   ├── test_agents.py
│   ├── test_sandbox.py
│   ├── test_skills.py
│   └── test_models.py
├── docs/
│   ├── ARCHITECTURE.md                # Detailed architecture
│   ├── SETUP_GUIDE.md                 # Step-by-step setup
│   ├── WORKFLOWS.md                   # Common workflows
│   ├── CUSTOMIZATION.md               # How to customize
│   ├── API_REFERENCE.md               # API docs
│   └── TROUBLESHOOTING.md             # Common issues
└── examples/
    ├── robot-walker/                  # Quadruped controller example
    ├── model-training/                # Fine-tuning workflow
    └── multi-agent-research/          # Parallel simulation sweep
```

## 💡 Common Workflows

### Workflow 1: Build a Feature Autonomously
```bash
# In Slack:
@openswe "Build authentication modal for login page"

# AI Dev OS:
1. Brainstorms design (Superpowers)
2. Creates implementation plan
3. Spawns subagents (code, tests, docs)
4. Validates in sandbox
5. Opens PR automatically
6. You review & merge
```

### Workflow 2: Fine-tune a Model
```python
from ai_dev_os import UnslothTrainer, BitNetInference

# Define training task
trainer = UnslothTrainer(
    model="meta-llama/Llama-2-7b",
    dataset="path/to/your/data.csv",
    output_quantization="1-bit"  # BitNet format
)

# Agent handles it
trainer.run_with_agent(
    sandbox="modal",
    monitor_hud=True  # Real-time Claude HUD updates
)
```

### Workflow 3: Robotics Simulation Sweep
```python
from ai_dev_os import NewtonSimulation, SubagentOrchestrator

# Define sweep parameters
sim = NewtonSimulation(
    robot="quadruped",
    terrain="stairs",
    episodes=1000
)

# Orchestrate parallel agents
orchestrator = SubagentOrchestrator(
    tasks=[
        ("sim", sim.config),
        ("train-policy", {"model": "Llama-8B", "bits": 4}),
        ("verify", {"metric": "success_rate", "threshold": 0.9})
    ],
    parallel=True,
    monitor_context=True  # Claude HUD watches context
)

results = orchestrator.run()
```

## 🔧 Configuration

### AGENTS.md (Per-Repo Rules)
```markdown
# AI Dev OS Rules for This Repo

## Tools
- Newton: enabled (GPU simulation)
- Unsloth: enabled (model training)
- BitNet: enabled (inference)

## Workflow Enforcement
- brainstorming: REQUIRED (design first)
- writing-plans: REQUIRED (plan before code)
- test-driven-development: REQUIRED (tests first)
- requesting-code-review: REQUIRED (review before merge)

## Thresholds
- context_warning: 75%
- context_critical: 90%
- test_coverage_min: 80%

## Custom Hooks
- pre_execution: validate AGENTS.md syntax
- post_merge: auto-update docs
```

### Claude HUD Config
Create `~/.claude/plugins/claude-hud/config.json`:
```json
{
  "lineLayout": "expanded",
  "pathLevels": 2,
  "elementOrder": ["project", "context", "usage", "tools", "agents", "todos"],
  "display": {
    "showModel": true,
    "showContextBar": true,
    "showTools": true,
    "showAgents": true,
    "showTodos": true,
    "showDuration": true,
    "showSpeed": true
  },
  "colors": {
    "context": "cyan",
    "usage": "cyan",
    "warning": "yellow",
    "critical": "red"
  }
}
```

## 📚 Documentation

- [**ARCHITECTURE.md**](ARCHITECTURE.md) - Deep dive into system design
- [**API_REFERENCE.md**](docs/API_REFERENCE.md) - API reference and interfaces
- [**DATA_CONTRACTS.md**](docs/DATA_CONTRACTS.md) - Data schemas and validation rules
- [**DEPENDENCY_STRATEGY.md**](docs/DEPENDENCY_STRATEGY.md) - Dependency management approach
- [**OBSERVABILITY_PLAN.md**](docs/OBSERVABILITY_PLAN.md) - Logging, metrics, and observability
- [**SECURITY_PLAN.md**](docs/SECURITY_PLAN.md) - Security practices and secrets management
- [**SETUP_GUIDE.md**](docs/SETUP_GUIDE.md) - Detailed installation for each OS
- [**VERSIONING.md**](docs/VERSIONING.md) - Versioning policy and release process
- [**WORKFLOWS.md**](docs/WORKFLOWS.md) - How to trigger and manage agent workflows
- [**CUSTOMIZATION.md**](docs/CUSTOMIZATION.md) - Extend with custom skills/tools
- [**ONBOARDING.md**](docs/ONBOARDING.md) - Guide for new contributors
- [**RUNBOOKS.md**](docs/RUNBOOKS.md) - Operational procedures and recovery steps
- [**TROUBLESHOOTING.md**](docs/TROUBLESHOOTING.md) - Debug common issues

## 🏆 Examples

### Example 1: Robot Walker
A complete end-to-end example building an autonomous quadruped controller.

```bash
cd examples/robot-walker
python run.py
```

See [`examples/robot-walker/README.md`](./examples/robot-walker/README.md) for details.

### Example 2: Model Fine-tuning
Fine-tune a model with Unsloth and quantize to BitNet format.

```bash
cd examples/model-training
python train.py --dataset ./data/custom.csv --output ./models/custom.gguf
```

### Example 3: Parallel Research
Run a research sweep across 1000 simulation configurations.

```bash
cd examples/multi-agent-research
python sweep.py --configs 1000 --parallel-agents 10
```

## 🔌 Integrations

### Slack
```bash
# In Slack, mention the bot:
@openswe "Your task here"
# Supports: repo:owner/name syntax for multi-repo
```

### Linear
```bash
# In Linear, comment on any issue:
@openswe "Fix the bug in production"
# Agent reads full context, posts results as comment
```

### GitHub
```bash
# Tag in PR comments:
@openswe "Address the review feedback"
# Agent fixes code and pushes to same branch
```

## 📊 Monitoring & Observability

### Claude HUD (Real-time)
Integrated into your terminal. Shows:
- Context usage (%) and remaining
- Active agents and their status
- Tools being used
- Todo progress
- Git branch and status

### Logs
```bash
# View agent execution logs
tail -f ~/.ai-dev-os/logs/agents.log

# View sandbox logs
tail -f ~/.ai-dev-os/logs/sandbox.log

# View model training progress
tail -f ~/.ai-dev-os/logs/training.log
```

### Dashboard (Optional)
```bash
uv run streamlit run app/dashboard.py
# Opens web UI at http://localhost:8501
# Features: Multi-user Auth, running agents, context usage, completed tasks, PR history
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test
uv run pytest tests/test_core_comprehensive.py
```

## 🚦 Status

- ✅ **Deep Agents orchestration**
- ✅ **Superpowers caching & workflow enforcement**
- ✅ **Unsloth training implementation** (Real fine-tuning)
- ✅ **BitNet inference** (Real CPU-optimized inference)
- ✅ **Web Dashboard** (Streamlit with multi-user Authentication)
- ✅ **Prometheus Monitoring**
- ✅ **GitHub OAuth flow & PR automation**
- ✅ **Slack/Linear invocation** with strict secret validation
- ✅ **Newton physics simulation**
- ✅ **Modern CI/CD** (`uv` based deterministic builds + Security gating with Bandit)
- ✅ **Daytona Sandbox Support** (Remote workspace orchestration)
- 🔜 Runloop sandbox support
- 🔜 Multi-GPU training optimization

## 🤝 Contributing

AI Dev OS is built by the community. To contribute:

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Follow [CONTRIBUTING.md](./CONTRIBUTING.md)
4. Submit a PR

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built on the shoulders of giants:
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Graph-based agent orchestration
- [Deep Agents](https://docs.anthropic.com/en/docs/build-with-claude/agents) - Agent framework
- [Superpowers](https://github.com/obra/superpowers) - Workflow skills
- [Claude HUD](https://github.com/jarrodwatts/claude-hud) - Terminal observability
- [Newton](https://github.com/newton-physics/newton) - Physics simulation
- [Unsloth](https://github.com/unslothai/unsloth) - Fast LLM training
- [BitNet](https://github.com/microsoft/BitNet) - Efficient inference

## 🔗 Links

- **Docs**: [ai-dev-os.dev](https://ai-dev-os.dev)
- **GitHub**: [Imposter-zx/ai-dev-os](https://github.com/Imposter-zx/ai-dev-os)
- **Discord**: [Community Server](https://discord.gg/ai-dev-os)
- **Twitter**: [@ai_dev_os](https://twitter.com/ai_dev_os)

---

**Ready to build with AI Dev OS?** Start with [SETUP_GUIDE.md](docs/SETUP_GUIDE.md) →