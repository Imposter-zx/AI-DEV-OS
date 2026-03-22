# AI Dev OS Agent Rules

This file defines the conventions and rules that autonomous agents in this repository must follow.

## Tools

### Enabled Tools
- **Newton**: GPU-accelerated physics simulation (optional, for robotics/simulation tasks)
- **Unsloth**: Fast model training and fine-tuning
- **BitNet**: 1-bit LLM inference (CPU-optimized)
- **Claude Code**: All Claude Code built-in tools (read_file, write_file, execute, etc.)

### Tool-Specific Rules

#### Newton (Simulation)
```yaml
- Environment: CUDA_VISIBLE_DEVICES must be set for multi-GPU
- Max Episodes: 1000 per run (parallel when possible)
- Output Format: Save metrics as JSON
```

#### Unsloth (Training)
```yaml
- Quantization Default: 4-bit (can use 1-bit for BitNet)
- Max Batch Size: Auto-tune based on GPU memory
- Save Format: Both safetensors and GGUF
```

#### BitNet (Inference)
```yaml
- Model Format: GGUF only
- Batch Size: 1 or 32 (no in-between)
- Context: Up to 4096 tokens
```

## Workflow Enforcement

### Phase 1: Brainstorming (REQUIRED)
- **Trigger**: Before any implementation
- **Rules**:
  - Ask clarifying questions via Socratic method
  - Explore at least 2 alternatives
  - Present design in chunks (short enough to digest)
  - Document: requirements, architecture, acceptance criteria
- **Outcome**: Design document approved by human

### Phase 2: Using Git Worktrees (REQUIRED)
- **Trigger**: After design approval
- **Rules**:
  - Create isolated branch from main
  - Run test baseline to verify green state
  - Do not commit to main directly
- **Outcome**: Clean worktree on feature branch

### Phase 3: Writing Plans (REQUIRED)
- **Trigger**: After design approval
- **Rules**:
  - Break work into tasks of 2-5 minutes each
  - Each task must include:
    - Exact file paths
    - Complete code snippets
    - Verification step (how to validate it works)
  - Prioritize: dependencies first, minimal viable first
- **Outcome**: Detailed implementation plan with task list

### Phase 4: Test-Driven Development (REQUIRED)
- **Trigger**: During implementation
- **Rules**:
  - RED: Write a failing test first
  - GREEN: Write minimal code to pass test
  - REFACTOR: Clean up code
  - Commit after GREEN state only
  - Delete any code written before tests exist
- **Coverage Target**: >= 80% of new code
- **Outcome**: All tests green before moving to next task

### Phase 5: Code Review (REQUIRED)
- **Trigger**: Before merging to main
- **Rules**:
  - Review against original plan
  - Report issues by severity: critical (blocks), major (should fix), minor (nice-to-have)
  - Verify all tests still pass
  - Check code follows repo style (black, isort, mypy)
- **Outcome**: Code review document with issues

### Phase 6: Finishing Development Branch (REQUIRED)
- **Trigger**: After code review approved
- **Rules**:
  - Verify all tests pass one final time
  - Create draft PR with:
    - Reference to original request
    - Summary of changes
    - Link to design doc
  - Preserve worktree for follow-up work
  - Or clean up worktree if fully done
- **Outcome**: PR merged or preserved for human review

## Context Window Management

- **Warning Threshold**: 75% context used → print warning, offer summary
- **Critical Threshold**: 90% context used → auto-summarize and commit
- **Max Context per Agent**: 100,000 tokens (reserve 10% for safety)

## Testing Requirements

### Mandatory Tests
- Unit tests for all new functions
- Integration tests for feature workflows
- Regression tests for existing functionality

### Test Framework
```yaml
Framework: pytest
Coverage: >= 80%
Async: Use pytest-asyncio
Mocking: Use pytest-mock for external calls
```

### Test Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_agents.py::test_brainstorming
```

## Code Style & Quality

### Python Style
- **Formatter**: Black (line length: 100)
- **Import Sorting**: isort (profile: black)
- **Linting**: flake8 (E501 disabled, max-line-length: 100)
- **Type Checking**: mypy (strict mode)

### Commands
```bash
black src/
isort src/
mypy src/
flake8 src/
```

## Git Conventions

### Commit Messages
```
Format: <type>(<scope>): <subject>

Types: feat, fix, docs, style, refactor, test, chore
Scope: module or feature name
Subject: lowercase, imperative, no period

Example: feat(agents): add brainstorming skill validation
```

### Branch Naming
```
Format: <type>/<description>
Examples:
- feature/add-newton-integration
- fix/context-window-overflow
- docs/update-api-reference
```

### PR Requirements
- [ ] All tests pass
- [ ] Coverage >= 80%
- [ ] Code review approved
- [ ] AGENTS.md updated (if rules changed)
- [ ] Documentation updated

## Performance Targets

### Model Training (Unsloth)
- **Speed**: >= 2x faster than standard training
- **VRAM**: <= 70% of standard requirements
- **Accuracy**: <= 0.1% loss compared to standard

### Inference (BitNet)
- **Latency**: < 50ms per token (CPU)
- **Throughput**: >= 5 tokens/sec (1-bit models)
- **Memory**: <= 2GB for 8B parameter models

### Simulation (Newton)
- **Throughput**: >= 1000 FPS per GPU
- **Accuracy**: Validated against real robot data

## Error Handling

### Required Behavior
1. Catch all exceptions explicitly (no bare `except:`)
2. Log full stack trace on error
3. Graceful degradation (don't crash, fail fast)
4. Retry once on transient failures (network, GPU out of memory)
5. Report errors to human after 2 retries

### Example
```python
try:
    result = await risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    # Retry logic
    # Fallback logic
    # Report to human
```

## Documentation Requirements

### Mandatory Documentation
- Module docstrings (describe purpose, usage)
- Function docstrings (describe parameters, returns, raises)
- Complex logic comments (explain why, not what)
- README for new features

### Example
```python
async def brainstorm_design(request: str) -> DesignDoc:
    """
    Refine a user's idea through Socratic questioning.
    
    Uses Claude to ask clarifying questions, explore alternatives,
    and generate a structured design document with requirements,
    architecture, and acceptance criteria.
    
    Args:
        request: User's initial request/idea
    
    Returns:
        DesignDoc with refined spec, requirements, and architecture
    
    Raises:
        ValueError: If request is empty or invalid
        APIError: If Claude API fails
    """
```

## Custom Hooks

### Pre-Execution Hook
```yaml
- Validates AGENTS.md syntax (JSON Schema)
- Checks for required fields (Tools, Workflow, Testing)
- Aborts if invalid
```

### Post-Merge Hook
```yaml
- Auto-updates docs/CHANGELOG.md
- Tags commit with version
- Triggers deployment workflow (if configured)
```

## Multi-Agent Coordination

### Subagent Context Isolation
- Each subagent has own context window (100k tokens max)
- Main agent coordinates via status file: `~/.ai-dev-os/hud_status.json`
- Agents do NOT share state directly (message-based only)

### Parallel Execution Rules
- Maximum 10 subagents in parallel (resource limit)
- Each agent isolated in sandbox (Modal, Docker, etc.)
- Failure of one agent doesn't stop others
- Main agent waits for all to complete before validation

### Communication Protocol
```yaml
Agent → Main: JSON status file
Main → Agent: Task description + context
Agents ↔ HUD: Real-time status updates
```

## Custom Thresholds

```yaml
context_warning: 75
context_critical: 90
test_coverage_min: 80
model_perplexity_max: 2.0  # For LLM fine-tuning validation
sim_success_rate_min: 0.85
```

## FAQ for Agents

**Q: What if I run out of context?**
A: Stop, save state, commit, and start fresh with task summary in new branch.

**Q: Should I ask for permission to commit?**
A: No. Commit after tests pass. Create PR for human review.

**Q: Can I skip tests for "simple" changes?**
A: No. TDD is mandatory. Even simple = simple test.

**Q: What if the design is wrong mid-implementation?**
A: Post comment to original issue/PR with findings, wait for human approval before changing direction.

**Q: Can I use GPT/Gemini/other LLMs?**
A: No. Use Claude only (via Anthropic API). No other providers.

---

**Version**: 1.1.0
**Last Updated**: 2026-03-22
**Maintained By**: AI Dev OS Build Team
