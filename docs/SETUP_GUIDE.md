# AI Dev OS Setup Guide

This guide provides detailed, step-by-step instructions for installing and configuring AI Dev OS across different operating systems.

## Prerequisites
Before you begin, ensure you have the following installed:
*   **Python 3.10 or higher**
*   **Git**
*   **Docker** (highly recommended for local sandboxes)
*   **(Optional)** NVIDIA GPU with CUDA drivers (required for Newton and Unsloth)

## 1. System Setup

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install build-essential python3-dev python3-venv git
# Install Docker if not present
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Windows
1.  Install [Python 3.10+](https://www.python.org/downloads/windows/). Ensure "Add Python to PATH" is checked.
2.  Install [Git for Windows](https://gitforwindows.org/).
3.  Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and enable WSL2 integration.

### macOS
```bash
# Using Homebrew
brew install python@3.10 git
# Install Docker
brew install --cask docker
```

## 2. Project Installation

We recommend using `uv` for lightning-fast, deterministic dependency resolution.

```bash
# Clone the repository
git clone https://github.com/Imposter-zx/ai-dev-os.git
cd ai-dev-os

# Create a virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync --all-groups
```

## 3. Configuration

Create a `.env` file in the root directory:
```bash
cp .env.example .env
```
Fill in the required tokens:
```env
ANTHROPIC_API_KEY=sk-ant-...        # Required for the core orchestrator
GITHUB_PAT=ghp_...                  # Optional: For repository interactions
SLACK_BOT_TOKEN=xoxb-...            # Optional: For Slack integration
DAYTONA_API_KEY=dyt_...             # Optional: For Daytona cloud sandboxes
MODAL_TOKEN_ID=...                  # Optional: For Modal cloud GPU
```

## 4. Sandbox Initialization

Decide where your AI agents will execute their code.

```bash
# For local Docker sandboxes (Recommended for getting started)
python scripts/setup-sandboxes.py --provider docker

# For remote cloud environments (Daytona)
python scripts/setup-sandboxes.py --provider daytona

# For GPU-intensive tasks (Modal)
python scripts/setup-sandboxes.py --provider modal
```

## 5. Next Steps
Once your environment is set up, head over to the [WORKFLOWS.md](WORKFLOWS.md) guide to learn how to trigger your first autonomous agent run!
