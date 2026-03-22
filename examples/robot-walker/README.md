# Robot Walker Example
This example demonstrates a complete end-to-end autonomous workflow where AI agents build a generic quadruped physics controller from scratch.

## Overview
This full-stack example orchestrates 3 distinct AI sub-agents to rapidly design, code, and valid a robot walking algorithm:
1.  **Code Agent**: Writes the Python controller referencing a physics engine module.
2.  **Training Agent**: Utilizes `Unsloth` to perform a miniature fine-tuning on behavioral navigation paths.
3.  **Simulation Agent**: Plugs the output into the `Newton` engine emulator to run validation sweeps.

## Running the Example
```bash
python run.py
```
This triggers the AI Dev OS central orchestrator to follow the strict `AGENTS.md` guidelines enforced within this example folder.
