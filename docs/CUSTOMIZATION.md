# Customizing AI Dev OS

AI Dev OS is designed to be highly extensible. You can add your own Superpower Skills, integrate custom Sandbox Providers, and write custom workflow hooks.

---

## 1. Creating Custom Superpower Skills

Skills dictate how the agent behaves during specific phases of development.

1.  Create a new Python file in `src/ai_dev_os/skills.py` (or inject it via configuration).
2.  Instantiate a `SuperpowerSkill` object.

```python
from ai_dev_os.core import SuperpowerSkill

my_custom_skill = SuperpowerSkill(
    name="systematic-debugging",
    trigger="When tests fail or bugs are reported",
    system_prompt=\"\"\"
    You are an elite debugging engineer. Follow these steps:
    1. Reproduce the error.
    2. Add extensive logging around the suspected failure point.
    3. Isolate the variable causing the crash.
    \"\"\"
)
```

Register this skill with the `AIDevOSOrchestrator` during initialization.

---

## 2. Adding a Custom Sandbox Provider

If you need to run code in an environment other than Docker, Modal, or Daytona, you can create a custom `Sandbox` subclass.

1.  Open `src/ai_dev_os/sandbox.py`.
2.  Subclass the `Sandbox` Abstract Base Class.

```python
from ai_dev_os.sandbox import Sandbox

class KubernetesSandbox(Sandbox):
    async def initialize(self) -> None:
        # Code to spin up a K8s pod
        pass

    async def execute(self, command: str) -> tuple[int, str, str]:
        # Code to exec into the pod and run the command
        return exit_code, stdout, stderr

    async def terminate(self) -> None:
        # Code to kill the pod
        pass
```

3.  Update the `SandboxProvider` enum and the `SandboxFactory` to recognize your new integration.

---

## 3. Defining Repository Rules (`AGENTS.md`)

The behavior of the autonomous agents can be controlled tightly by the `AGENTS.md` file located in the root of your target repository.

The orchestrator reads this file at startup. You can customize:
*   **Mandatory testing frameworks** (e.g., changing `pytest` to `unittest`).
*   **Code coverage targets** (e.g., `80%` vs `100%`).
*   **Code formatting rules** (e.g., `black` vs `ruff`).

Agents are strictly instructed to read your `AGENTS.md` and comply with its rules before execution.
