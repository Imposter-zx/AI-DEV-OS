# Multi-Agent Research Sweep

This example shows how to orchestrate 10+ parallel agents to perform a large-scale simulation sweep using `Newton`.

## Usage
```bash
python sweep.py --configs 1000 --parallel-agents 10
```

## Workflow
1. Orchestrator spawns 10 subagents.
2. Each agent runs 100 simulations in a Modal sandbox.
3. Results are aggregated and visualized in Claude HUD.
