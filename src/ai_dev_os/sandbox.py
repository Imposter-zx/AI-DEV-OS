"""
Sandbox abstraction layer - supports Modal, Daytona, Runloop, Docker.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


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
        pass

    @abstractmethod
    async def execute(self, command: str, cwd: str = "/workspace") -> Tuple[int, str, str]:
        """
        Execute a command in the sandbox.
        Returns: (exit_code, stdout, stderr)
        """
        pass

    @abstractmethod
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file to the sandbox."""
        pass

    @abstractmethod
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file from the sandbox."""
        pass

    @abstractmethod
    async def terminate(self) -> bool:
        """Terminate the sandbox."""
        pass

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
        """Execute command in Modal."""
        try:
            # In production, use modal.run to execute
            # For now, return mock response
            self.add_log(f"Executing: {command}")

            # Mock execution
            await asyncio.sleep(0.5)

            return (0, f"[mock] {command} completed", "")

        except Exception as e:
            self.status = SandboxStatus.ERROR
            self.add_log(f"Execution failed: {str(e)}")
            return (1, "", str(e))

    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to Modal sandbox."""
        try:
            self.add_log(f"Uploading {local_path} to {remote_path}")
            # In production, use modal file mounting
            return True
        except Exception as e:
            self.add_log(f"Upload failed: {str(e)}")
            return False

    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from Modal sandbox."""
        try:
            self.add_log(f"Downloading {remote_path} to {local_path}")
            # In production, retrieve from Modal
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

    async def initialize(self) -> str:
        """Initialize a Daytona sandbox."""
        try:
            # Placeholder for Daytona API integration
            self.id = f"daytona-{self.config.name}"
            self.status = SandboxStatus.READY
            self.add_log(f"Daytona sandbox initialized: {self.id}")
            return self.id
        except Exception as e:
            self.status = SandboxStatus.ERROR
            self.add_log(f"Initialization failed: {str(e)}")
            raise

    async def execute(self, command: str, cwd: str = "/workspace") -> Tuple[int, str, str]:
        """Execute command in Daytona."""
        try:
            self.add_log(f"Executing: {command}")
            await asyncio.sleep(0.5)
            return (0, f"[daytona] {command} completed", "")
        except Exception as e:
            return (1, "", str(e))

    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to Daytona."""
        try:
            self.add_log(f"Uploading {local_path}")
            return True
        except Exception as e:
            self.add_log(f"Upload failed: {str(e)}")
            return False

    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from Daytona."""
        try:
            self.add_log(f"Downloading {remote_path}")
            return True
        except Exception as e:
            self.add_log(f"Download failed: {str(e)}")
            return False

    async def terminate(self) -> bool:
        """Terminate Daytona sandbox."""
        try:
            self.add_log("Terminating Daytona sandbox")
            self.status = SandboxStatus.TERMINATED
            return True
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

            exit_code, output = self.container.exec_run(
                f"bash -c 'cd {cwd} && {command}'", stdout=True, stderr=True
            )

            stdout = output.decode() if isinstance(output, bytes) else str(output)

            return (exit_code, stdout, "")

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
