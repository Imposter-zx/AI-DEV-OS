AI Dev OS — Architecture Overview

Overview
- AI Dev OS is a production-ready orchestrator for autonomous AI workflows. It coordinates a core set of components (core orchestrator, sandbox/runtime sandboxes, model wrappers, integrations, and observability) to enable end-to-end engineering pipelines.

Key Components
- Core Orchestrator: Central coordination and state management for the entire workflow.
- Sandboxes: Isolated execution environments (Modal, Docker, etc.) for running subagents safely.
- Models: Wrappers around training/inference primitives (Unsloth, BitNet).
- Integrations: Slack/Linear/GitHub adapters for external triggers and notifications.
- HUD/Observability: Real-time status updates and metrics surfaced to users.
- Data Contracts: Validation and serialization boundaries between components using pydantic-like models.

Data Flow (high level)
- User request → Brainstorming → Planning → Execution (Code/Train/Sim) → Validation → HUD updates → PR/Deployment

Interfaces
- Public: orchestrator API surface for subagents and integrations.
- Internal: message passing, event streams, and lifecycle hooks for sandboxes.

Notes
- This document is a living artifact and should be updated as architecture decisions evolve.
