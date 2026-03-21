# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Web Dashboard**: Streamlit interface to monitor agents and workflows.
- **Monitoring**: Prometheus metrics wrapper.
- **Integrations**: Slack, Linear, and GitHub OAuth integrations.
- **Core Tests**: Comprehensive test suite covering orchestrator and workflows.
- **Real Training**: Unsloth fine-tuning via `SFTTrainer`.
- **Real Inference**: CPU-optimized `llama-cpp` BitNet inference.
- **CI/CD**: Expanded GitHub Actions using `uv`.
- **Simulation**: Support for Newton physics simulations.
- **Templates**: Add bug/feature reporting templates and PR guidelines.
- **Security**: Added `SECURITY.md`.

### Changed
- Migrated dependency management from `requirements.txt` to `pyproject.toml` (via `uv`).
- Standardized imports, removing `sys.path` injection hacks.

### Fixed
- Logging configuration compatibility across different `python-json-logger` versions.
