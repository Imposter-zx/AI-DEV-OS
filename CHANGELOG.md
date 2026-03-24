# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-03-24
### Added
- **LLM-Agnostic Engine**: Introduced `BaseLLM` with `AnthropicLLM` and `LocalLLM` (llama.cpp) implementations into `core.py`.
- **True Agent Tooling**: Orchestrator sub-agents now utilize real iterative JSON-based tool loops to execute filesystem and shell logic dynamically.
- **Hardware Integration**: Unsloth training, BitNet inferences, and Newton physics now enforce physical execution requirements, removing prior `asyncio` simulation mocks.
- **Sandbox Reality**: Replaced simulated sleeps with real `modal.Function` allocation and containerized local `DockerSandbox` execution streams.

## [1.1.0] - 2026-03-22
### Added
- GitHub Integration (OAuth, PRs, Commits).
- Slack Bot (Threads, Interactive, Slash).
- Linear Integration (Issue creation, Status updates).
- Error Recovery (Snapshots, Retries).
- Advanced Superpowers Skills (Research, Audit, Optimization).
- Advanced Context Management (Token tracking, Summarization).
- Daytona Sandbox Integration.
- Comprehensive Testing Suite (50+ tests).

## [1.0.0] - 2024-01-01
### Initial Release
- Core orchestrator engine.
- Modal and Docker sandbox support.
- Basic brainstorming and planning skills.
