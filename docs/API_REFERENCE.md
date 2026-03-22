# AI Dev OS API Reference

This document provides an overview of the core classes and methods available in the `ai-dev-os` package.

---

## `ai_dev_os.core`

### `class AIDevOSOrchestrator`
The main entry point for running autonomous workflows.

#### `__init__(self, sandbox_provider: str = "(auto)", override_rules_path: str = None)`
Initializes the orchestrator, loads Superpower Skills, and sets up the primary context manager.
*   **Args:**
    *   `sandbox_provider`: Force a specific sandbox provider (`docker`, `modal`, `daytona`). Defaults to auto-detection from `AGENTS.md`.
    *   `override_rules_path`: Path to an alternative `AGENTS.md` rules file.

#### `async run(self, objective: str) -> WorkflowState`
Begins an autonomous workflow.
*   **Args:**
    *   `objective`: The user's request, feature, or bug description.
*   **Returns:**
    *   The final `WorkflowState` object after execution completes or fails.

---

## `ai_dev_os.sandbox`

### `class SandboxFactory`
Generates isolated execution environments.

#### `static async create_sandbox(provider: str, task_name: str) -> Sandbox`
Create a new Sandbox instance based on the provider string.
*   **Args:**
    *   `provider`: String representing the provider (e.g., `"docker"`, `"modal"`).
    *   `task_name`: A descriptive name for the sandbox to tag containers/workloads.

### `class Sandbox (ABC)`
Abstract base class for all sandboxes. Subclasses include `DockerSandbox`, `ModalSandbox`, and `DaytonaSandbox`.

#### `async execute(self, command: str, cwd: str = None) -> tuple[int, str, str]`
Executes a bash command within the sandbox.
*   **Args:**
    *   `command`: The bash command to run.
    *   `cwd`: The working directory to execute the command in.
*   **Returns:**
    *   A tuple containing `(exit_code: int, stdout: str, stderr: str)`.

---

## `ai_dev_os.models`

### `class UnslothTrainer`
Automates fast model fine-tuning with automatic BitNet quantization.

#### `__init__(self, config: dict)`
Initializes the trainer with hyperparameters.
*   **Args:**
    *   `config`: Dictionary of Unsloth parameters (batch size, learning rate, bits).

#### `async train(self) -> tuple[bool, dict]`
Begins the training loop.
*   **Returns:**
    *   Tuple of `(success_boolean, metrics_dictionary)`.

---

## `ai_dev_os.utils.context`

### `class ContextManager`
Tracks token usage and summarizes history.

#### `def record_usage(self, input_tokens: int, output_tokens: int) -> None`
Records token spend for Anthropic API reporting and cost estimations.
