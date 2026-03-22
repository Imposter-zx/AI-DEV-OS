# AI Dev OS Workflows

This document outlines how to trigger, manage, and monitor the autonomous workflows within AI Dev OS.

## The Core Pipeline
Every task processed by AI Dev OS follows a strict, mandatory pipeline defined by the **Superpowers** skill framework:

1.  **Brainstorming**: Refines the user's initial request. Asks clarifying questions using the Socratic method and produces a Design Document.
2.  **Planning**: Breaks the approved design into 2-5 minute tasks. Identifies files to edit and creates a Test-Driven Development (TDD) plan.
3.  **Execution** (Parallel): Splits the plan across multiple subagents running in isolated sandboxes.
4.  **Code Review**: Validates the output against the original plan, runs the test suite, and enforces repo style rules (`black`, `isort`, `mypy`).
5.  **Merge**: Auto-creates a PR or merges the feature branch if all gates pass.

---

## Triggering Workflows

### 1. Python CLI
You can start a workflow interactively from your terminal:
```bash
python -m ai_dev_os.core
```
You will be prompted to enter your requested feature or bug fix.

### 2. Slack Integration
If you have configured the Slack Bot, you can tag the bot in any channel:
```
@openswe "Build a new authentication flow using JWT"
```
The bot will reply in a thread, updating its status as it progresses through the pipeline phases.

### 3. Linear Issue Tracking
When an issue is assigned to the `openswe` user or tagged with `ai-dev-os`, the system will automatically pick it up, read the issue description as the objective, and post comments as it completes tasks.

---

## Managing Sandbox Execution

By default, the `SubagentOrchestrator` runs tasks in parallel (up to 10 max).
You can customize the execution phase by modifying the `AGENTS.md` file in your repository:

```yaml
# Parallel Execution Rules
- Maximum 10 subagents in parallel
- Agent failure isolating (Failure of one won't stop others; orchestrator retries).
```

## Real-Time Monitoring (Claude HUD)

AI Dev OS integrates with the **Claude HUD** to provide terminal-level observability.

As an agent runs, your terminal will display:
*   **Context usage bar**: Visual representation of the 100k token limit.
*   **Action tracking**: What files the agent is currently viewing or editing.
*   **Pipeline phase**: Current progress through the Brainstorming -> Review pipeline.

*Note: If context usage hits 90% (Critical Threshold), the system will automatically summarize its context, commit its current state, and start fresh.*
