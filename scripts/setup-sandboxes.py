#!/usr/bin/env python3
"""
Setup script for AI Dev OS - initializes sandboxes, plugins, and config.

Usage:
    python scripts/setup-sandboxes.py --provider modal
    python scripts/setup-sandboxes.py --provider docker
"""

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def setup_claude_hud_config():
    """Setup Claude HUD configuration."""
    hud_config_dir = Path.home() / ".claude" / "plugins" / "claude-hud"
    hud_config_dir.mkdir(parents=True, exist_ok=True)
    
    config_file = hud_config_dir / "config.json"
    
    if config_file.exists():
        logger.info(f"Claude HUD config already exists at {config_file}")
        return
    
    config = {
        "lineLayout": "expanded",
        "pathLevels": 2,
        "elementOrder": ["project", "context", "usage", "tools", "agents", "todos"],
        "gitStatus": {
            "enabled": True,
            "showDirty": True,
            "showAheadBehind": False,
            "showFileStats": False
        },
        "display": {
            "showModel": True,
            "showContextBar": True,
            "showConfigCounts": False,
            "showDuration": True,
            "showSpeed": False,
            "showUsage": True,
            "showTools": True,
            "showAgents": True,
            "showTodos": True,
            "showSessionName": False
        },
        "colors": {
            "context": "cyan",
            "usage": "cyan",
            "warning": "yellow",
            "usageWarning": "brightMagenta",
            "critical": "red"
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"✓ Claude HUD config created at {config_file}")


def setup_local_directories():
    """Setup required local directories."""
    dirs = [
        Path.home() / ".ai-dev-os",
        Path.home() / ".ai-dev-os" / "logs",
        Path.home() / ".ai-dev-os" / "models",
        Path.home() / ".ai-dev-os" / "checkpoints",
        Path.cwd() / ".ai-dev-os",
        Path.cwd() / ".ai-dev-os" / "data",
        Path.cwd() / ".ai-dev-os" / "results",
    ]
    
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Directory created: {directory}")


async def test_modal_setup():
    """Test Modal sandbox setup."""
    logger.info("Testing Modal setup...")
    
    try:
        import modal
        logger.info("✓ Modal SDK installed")
        
        # Test authentication
        if os.environ.get("MODAL_TOKEN_ID") and os.environ.get("MODAL_TOKEN_SECRET"):
            logger.info("✓ Modal credentials detected")
        else:
            logger.warning("⚠ Modal credentials not found. Run: modal token new")
        
        return True
    except ImportError:
        logger.error("✗ Modal not installed. Run: pip install modal")
        return False


async def test_docker_setup():
    """Test Docker sandbox setup."""
    logger.info("Testing Docker setup...")
    
    try:
        import docker
        client = docker.from_env()
        client.ping()
        logger.info("✓ Docker is running")
        return True
    except ImportError:
        logger.error("✗ Docker SDK not installed. Run: pip install docker")
        return False
    except Exception as e:
        logger.error(f"✗ Docker error: {str(e)}")
        return False


async def test_anthropic_setup():
    """Test Anthropic API setup."""
    logger.info("Testing Anthropic API setup...")
    
    try:
        import anthropic
        
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("✗ ANTHROPIC_API_KEY not set")
            return False
        
        client = anthropic.Anthropic()
        # Test with a simple message
        response = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        logger.info("✓ Anthropic API working")
        return True
    except Exception as e:
        logger.error(f"✗ Anthropic API error: {str(e)}")
        return False


def create_env_file():
    """Create .env file template if it doesn't exist."""
    env_file = Path.cwd() / ".env"
    
    if env_file.exists():
        logger.info(f"✓ .env file already exists")
        return
    
    env_content = """# AI Dev OS Environment Variables

# Anthropic API
ANTHROPIC_API_KEY=sk-...  # Set your API key here

# Modal (optional)
# MODAL_TOKEN_ID=...
# MODAL_TOKEN_SECRET=...

# Model Paths
MODEL_OUTPUT_DIR=./models
CHECKPOINT_DIR=./checkpoints

# Sandbox Configuration
SANDBOX_PROVIDER=docker  # or modal, daytona, runloop
SANDBOX_TIMEOUT_SECONDS=3600
SANDBOX_MEMORY_GB=8
SANDBOX_GPU=false

# Logging
LOG_LEVEL=INFO
LOG_DIR=~/.ai-dev-os/logs

# Development
DEBUG=false
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    logger.info(f"✓ .env file created. Please edit with your configuration.")


async def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup AI Dev OS")
    parser.add_argument(
        "--provider",
        choices=["modal", "docker", "both"],
        default="docker",
        help="Sandbox provider to test"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip provider tests"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("AI Dev OS Setup")
    logger.info("=" * 60)
    
    # Setup directories and config
    logger.info("\n[1/4] Setting up directories...")
    setup_local_directories()
    
    logger.info("\n[2/4] Setting up Claude HUD...")
    setup_claude_hud_config()
    
    logger.info("\n[3/4] Creating .env file...")
    create_env_file()
    
    logger.info("\n[4/4] Testing providers...")
    
    if not args.skip_tests:
        results = {}
        
        if args.provider in ["modal", "both"]:
            results["modal"] = await test_modal_setup()
        
        if args.provider in ["docker", "both"]:
            results["docker"] = await test_docker_setup()
        
        # Always test Anthropic
        results["anthropic"] = await test_anthropic_setup()
        
        logger.info("\n" + "=" * 60)
        logger.info("Setup Status")
        logger.info("=" * 60)
        
        for provider, success in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            logger.info(f"{status}: {provider}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Setup Complete!")
    logger.info("=" * 60)
    logger.info("""
Next steps:
1. Edit .env with your API keys
2. Read docs/SETUP_GUIDE.md for detailed setup
3. Try: python -m ai_dev_os.core
4. Or start Claude Code and run: @openswe "Build something"
    """)


if __name__ == "__main__":
    asyncio.run(main())
