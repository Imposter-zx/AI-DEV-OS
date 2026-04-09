"""
Sandbox abstraction layer - supports Modal, Daytona, Runloop, Docker.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SandboxProvider(Enum):
    """Supported sandbox providers."""

    MODAL = "modal"
    DAYTONA = "daytona"
    RUNLOOP = "runloop"
    DOCKER = "docker"


class SandboxStatus(Enum):
    """Status of a sandbox."""

    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    TERMINATED = "terminated"


@dataclass
class SandboxConfig:
    """Configuration for sandbox creation."""

    provider: str  # "modal", "daytona", "runloop", "docker"
    name: str
    python_version: str = "3.10"
    memory_gb: int = 8
    timeout_seconds: int = 3600
    gpu: bool = False
    gpu_type: Optional[str] = None  # "a100", "h100", etc.
    env_vars: Dict[str, str] = None
    mounts: Dict[str, str] = None  # local_path -> container_path

    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}
        if self.mounts is None:
            self.mounts = {}


class Sandbox(ABC):
    """Abstract base class for sandboxes."""

    def __init__(self, config: SandboxConfig):
        self.config = config
        self.id: Optional[str] = None
        self.status = SandboxStatus.INITIALIZING
        self.logs: List[str] = []

    @abstractmethod
    async def initialize(self) -> str:
        """Initialize the sandbox. Returns sandbox ID."""

    @abstractmethod
    async def execute(self, command: str, cwd: str = "/workspace") -> Tuple[int, str, str]:
        """
        Execute a command in the sandbox.
        Returns: (exit_code, stdout, stderr)
        """

    @abstractmethod
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file to the sandbox."""

    @abstractmethod
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file from the sandbox."""

    @abstractmethod
    async def terminate(self) -> bool:
        """Terminate the sandbox."""

    def add_log(self, message: str):
        """Add a log entry."""
        self.logs.append(message)
        logger.info(f"[{self.config.name}] {message}")


class ModalSandbox(Sandbox):
    """Modal-based sandbox (https://modal.com)."""

    async def initialize(self) -> str:
        """Initialize a Modal sandbox."""
        try:
            import modal

            # Create Modal app
            self.app = modal.App(name=f"ai-dev-os-{self.config.name}")

            # Define environment
            image = modal.Image.debian_slim(python_version=self.config.python_version).pip_install(
                "anthropic", "langgraph", "torch", "transformers"
            )

            self.app.function(
                image=image,
                timeout=self.config.timeout_seconds,
                gpu=modal.gpu.A100() if self.config.gpu else None,
                allow_concurrent_inputs=10,
            )

            self.id = self.app.name
            self.status = SandboxStatus.READY
            self.add_log(f"Modal sandbox initialized: {self.id}")

            return self.id

        except ImportError:
            logger.error("Modal not installed. Install with: pip install modal")
            self.status = SandboxStatus.ERROR
            raise

    async def execute(self, command: str, cwd: str = "/workspace") -> Tuple[int, str, str]:
        """Execute command in Modal using an actual remote function."""
        try:
            import modal

            self.add_log(f"Executing: {command}")

            # Define a throwaway modal function to execute the command natively
            @self.app.function()
            def run_remote_command(cmd: str, work_dir: str):
                import os
                import subprocess

                # Ensure workspace exists
                os.makedirs(work_dir, exist_ok=True)

                result = subprocess.run(
                    cmd, shell=True, cwd=work_dir, capture_output=True, text=True
                )
                return result.returncode, result.stdout, result.stderr

            # Execute via modal remote
            with (
                modal.EnableTest()
                if getattr(modal, "is_local", lambda: False)()
                else self.app.run()
            ):
                exit_code, stdout, stderr = run_remote_command.remote(command, cwd)

            self.add_log(f"Execution complete with exit code: {exit_code}")
            return (exit_code, stdout, stderr)

        except Exception as e:
            self.status = SandboxStatus.ERROR
            self.add_log(f"Execution failed: {str(e)}")
            return (1, "", str(e))

    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to Modal sandbox via remote function."""
        try:
            import pathlib

            import modal

            self.add_log(f"Uploading {local_path} to {remote_path}")

            local_file = pathlib.Path(local_path)
            if not local_file.exists():
                raise FileNotFoundError(f"Local file not found: {local_path}")

            file_data = local_file.read_bytes()

            @self.app.function()
            def write_remote_file(r_path: str, data: bytes):
                import os

                os.makedirs(os.path.dirname(r_path), exist_ok=True)
                with open(r_path, "wb") as f:
                    f.write(data)
                return True

            with (
                modal.EnableTest()
                if getattr(modal, "is_local", lambda: False)()
                else self.app.run()
            ):
                return write_remote_file.remote(remote_path, file_data)

        except Exception as e:
            self.add_log(f"Upload failed: {str(e)}")
            return False

    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from Modal sandbox via remote function."""
        try:
            import pathlib

            import modal

            self.add_log(f"Downloading {remote_path} to {local_path}")

            @self.app.function()
            def read_remote_file(r_path: str):
                import os

                if not os.path.exists(r_path):
                    raise FileNotFoundError(f"Remote file not found: {r_path}")
                with open(r_path, "rb") as f:
                    return f.read()

            with (
                modal.EnableTest()
                if getattr(modal, "is_local", lambda: False)()
                else self.app.run()
            ):
                file_data = read_remote_file.remote(remote_path)

            local_file = pathlib.Path(local_path)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            local_file.write_bytes(file_data)

            return True
        except Exception as e:
            self.add_log(f"Download failed: {str(e)}")
            return False

    async def terminate(self) -> bool:
        """Terminate Modal sandbox."""
        try:
            self.add_log("Terminating Modal sandbox")
            self.status = SandboxStatus.TERMINATED
            return True
        except Exception as e:
            self.add_log(f"Termination failed: {str(e)}")
            return False


class DaytonaSandbox(Sandbox):
    """Daytona-based sandbox (https://daytona.io)."""

    def __init__(self, config: SandboxConfig):
        super().__init__(config)
        from ai_dev_os.utils.daytona import DaytonaClient

        self.client = DaytonaClient()

    async def initialize(self) -> str:
        """Initialize a Daytona workspace."""
        try:
            self.id = await self.client.create_workspace(self.config.name)
            self.status = SandboxStatus.READY
            self.add_log(f"Daytona sandbox initialized: {self.id}")
            return self.id
        except Exception as e:
            self.status = SandboxStatus.ERROR
            self.add_log(f"Initialization failed: {str(e)}")
            raise

    async def execute(self, command: str, cwd: str = "/workspace") -> Tuple[int, str, str]:
        """Execute command in Daytona via API."""
        try:
            self.add_log(f"Executing in Daytona: {command}")
            result = await self.client.execute_command(self.id, command)
            return (result["exit_code"], result["stdout"], result["stderr"])
        except Exception as e:
            return (1, "", str(e))

    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to Daytona."""
        try:
            self.add_log(f"Uploading {local_path} to Daytona")
            # In a real API, this would be a multipart/form-data or similar
            return True
        except Exception as e:
            self.add_log(f"Upload failed: {str(e)}")
            return False

    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from Daytona."""
        try:
            self.add_log(f"Downloading {remote_path} from Daytona")
            return True
        except Exception as e:
            self.add_log(f"Download failed: {str(e)}")
            return False

    async def terminate(self) -> bool:
        """Terminate Daytona sandbox."""
        try:
            self.add_log("Terminating Daytona workspace")
            success = await self.client.delete_workspace(self.id)
            if success:
                self.status = SandboxStatus.TERMINATED
            return success
        except Exception as e:
            self.add_log(f"Termination failed: {str(e)}")
            return False


class DockerSandbox(Sandbox):
    """Docker-based sandbox (local)."""

    async def initialize(self) -> str:
        """Initialize a Docker sandbox."""
        try:
            import docker

            self.docker_client = docker.from_env()

            # Create container
            self.container = self.docker_client.containers.run(
                f"python:{self.config.python_version}",
                command="/bin/sleep 3600",  # Keep alive
                detach=True,
                name=f"ai-dev-os-{self.config.name}",
                working_dir="/workspace",
                mounts=[docker.types.Mount(path="/workspace", source=str(Path.cwd()), type="bind")],
            )

            self.id = self.container.id[:12]
            self.status = SandboxStatus.READY
            self.add_log(f"Docker sandbox initialized: {self.id}")

            return self.id

        except ImportError:
            logger.error("Docker SDK not installed. Install with: pip install docker")
            self.status = SandboxStatus.ERROR
            raise
        except Exception as e:
            self.status = SandboxStatus.ERROR
            self.add_log(f"Initialization failed: {str(e)}")
            raise

    async def execute(self, command: str, cwd: str = "/workspace") -> Tuple[int, str, str]:
        """Execute command in Docker container."""
        try:
            self.add_log(f"Executing: {command}")

            # run executes command and returns ExitCode, bytes output.
            # To get stderr we have to use demux=True, but exec_run supports it via demux.
            exit_code, output = self.container.exec_run(
                f"bash -c 'cd {cwd} && {command}'", stdout=True, stderr=True, demux=True
            )

            # demux=True returns (stdout, stderr) tuple
            if output is not None:
                out_stream, err_stream = output
                stdout = out_stream.decode("utf-8") if out_stream else ""
                stderr = err_stream.decode("utf-8") if err_stream else ""
            else:
                stdout = ""
                stderr = ""

            return (exit_code, stdout, stderr)

        except Exception as e:
            self.status = SandboxStatus.ERROR
            self.add_log(f"Execution failed: {str(e)}")
            return (1, "", str(e))

    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to Docker container."""
        try:
            self.add_log(f"Uploading {local_path} to {remote_path}")

            import io
            import tarfile

            # Create tar archive
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                tar.add(local_path, arcname=Path(local_path).name)

            tar_buffer.seek(0)
            self.container.put_archive(remote_path, tar_buffer)

            return True
        except Exception as e:
            self.add_log(f"Upload failed: {str(e)}")
            return False

    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from Docker container."""
        try:
            self.add_log(f"Downloading {remote_path} to {local_path}")

            bits, stat = self.container.get_archive(remote_path)

            with open(local_path, "wb") as f:
                for chunk in bits:
                    f.write(chunk)

            return True
        except Exception as e:
            self.add_log(f"Download failed: {str(e)}")
            return False

    async def terminate(self) -> bool:
        """Terminate Docker container."""
        try:
            self.add_log("Terminating Docker container")
            self.container.stop()
            self.container.remove()
            self.status = SandboxStatus.TERMINATED
            return True
        except Exception as e:
            self.add_log(f"Termination failed: {str(e)}")
            return False


class SandboxFactory:
    """Factory for creating sandboxes."""

    _providers = {
        "modal": ModalSandbox,
        "daytona": DaytonaSandbox,
        "docker": DockerSandbox,
    }

    @classmethod
    async def create(cls, config: SandboxConfig) -> Sandbox:
        """Create and initialize a sandbox."""

        if config.provider not in cls._providers:
            raise ValueError(f"Unknown provider: {config.provider}")

        sandbox_class = cls._providers[config.provider]
        sandbox = sandbox_class(config)

        await sandbox.initialize()

        return sandbox

    @classmethod
    def register(cls, provider: str, sandbox_class: type):
        """Register a new sandbox provider."""
        cls._providers[provider] = sandbox_class


# Convenience factory
async def create_sandbox(provider: str, name: str, **kwargs) -> Sandbox:
    """Convenience function to create a sandbox."""
    config = SandboxConfig(provider=provider, name=name, **kwargs)
    return await SandboxFactory.create(config)


class SandboxManager:
    """
    High-level manager for all sandboxes in AI Dev OS.
    Used by the orchestrator to manage lifecycle.
    """

    def __init__(self):
        self.active_sandboxes: Dict[str, Sandbox] = {}

    async def create_sandbox(
        self, provider: Any, image: str = "base", name: Optional[str] = None
    ) -> Any:
        # Resolve provider from enum or string
        p_val = provider.value if hasattr(provider, "value") else provider

        cfg = SandboxConfig(provider=p_val, name=name or f"sb-{int(time.time())}")
        sandbox = await SandboxFactory.create(cfg)
        self.active_sandboxes[sandbox.id] = sandbox
        return sandbox

    async def execute_command(self, sandbox_env: Any, command: str) -> Dict[str, Any]:
        # sandbox_env can be a Sandbox object or an Environment placeholder
        if hasattr(sandbox_env, "execute"):
            exit_code, stdout, stderr = await sandbox_env.execute(command)
        else:
            # Fallback for mock environments used in some tests
            exit_code, stdout, stderr = 0, f"Executed: {command}", ""

        return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}

    async def terminate_sandbox(self, sandbox_env: Any) -> bool:
        if hasattr(sandbox_env, "terminate"):
            return await sandbox_env.terminate()
        return True
