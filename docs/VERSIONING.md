# Versioning Policy

## Overview
AI Dev OS follows Semantic Versioning (SemVer) for release versioning. This document outlines our versioning strategy, release process, and compatibility guarantees.

## Version Format
Versions follow the format: **MAJOR.MINOR.PATCH**

- **MAJOR**: Incompatible API changes, breaking changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes

### Examples
- `0.1.0` → Initial development release
- `0.2.0` → Added new integration (backward compatible)
- `0.2.1` → Fixed bug in orchestrator (patch)
- `1.0.0` → First stable release (may break from 0.x)
- `1.1.0` → Added sandbox enhancements (minor)

## Pre-Release Versions
During development, we may use pre-release identifiers:
- **alpha**: Early testing, unstable features (`1.0.0-alpha.1`)
- **beta**: Feature complete, testing (`1.0.0-beta.2`)
- **rc**: Release candidate, pre-final (`1.0.0-rc.1`)

Pre-release versions sort before the associated release version.

## Build Metadata
We may include build metadata for internal tracking:
- `1.0.0+20260405.1` (build timestamp and counter)
- Build metadata is ignored in version precedence

## Compatibility Guarantees

### Public API
- Defined as: Public classes, functions, and CLI commands in `ai_dev_os` package
- MINOR and PATCH versions guarantee backward compatibility
- MAJOR versions may break public API with migration guidance

### Data Contracts
- Follow SemVer principles for schema evolution
- Optional fields can be added in PATCH/MINOR
- Required field changes require MAJOR version
- Deprecation period of at least one MINOR version for removed fields

### Configuration
- Configuration file format changes follow SemVer
- New options can be added in PATCH/MINOR
- Removed options require deprecation period
- Environment variable names treated as public API

## Release Process

### Version Bumping
1. Determine version bump type based on changes
2. Update `pyproject.toml` version field
3. Add entry to `CHANGELOG.md`
4. Commit changes with version bump
5. Tag release: `vMAJOR.MINOR.PATCH`
6. Push tags to trigger automated release

### Release Tags
- Format: `vMAJOR.MINOR.PATCH` (e.g., `v1.0.0`)
- Pre-releases: `vMAJOR.MINOR.PATCH-rc.1`
- Only signed releases from maintainers

## Branching Strategy

### Main Branch
- `main`: Always represents latest stable release
- All changes merged via pull requests
- CI must pass before merging

### Development Work
- Feature branches: `feature/descriptive-name`
- Bug fix branches: `fix/issue-number-description`
- Release branches: `release/vMAJOR.MINOR.PATCH` (for patch releases)

### Release Branches
Used for patch releases when main has progressed:
- Created from relevant tag
- Contains only critical fixes
- Merged back to main after release

## Changelog Format

### Keep a Changelog
We follow [Keep a Changelog](https://keepachangelog.com/) format:

```
# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- New feature description
### Changed
- Changed feature description
### Fixed
- Bug fix description
### Removed
- Removed feature description

## [1.0.0] - 2026-04-05
### Added
- Initial release
```

### Entry Types
- **Added**: For new features
- **Changed**: For changes in existing functionality
- **Fixed**: For bug fixes
- **Removed**: For removed features
- **Deprecated**: For soon-to-be removed features
- **Security**: For security vulnerabilities

## Release Cadence

### Development Releases
- Frequent during active development
- At least weekly during sprint cycles
- Available as pre-release versions

### Stable Releases
- Monthly or bi-monthly depending on feature completion
- Aligned with sprint demos and milestones
- Promoted from release candidates

### Patch Releases
- As needed for critical bug fixes
- Security patches released immediately
- Minor bug fixes batched for efficiency

## Version Determination Guidelines

### MAJOR Version Bump
- Breaking changes to public API
- Removal of deprecated features
- Major architectural changes
- Changes to data contract requirements

### MINOR Version Bump
- New features or enhancements
- New integrations or sandbox types
- Significant performance improvements
- New public APIs or CLI commands

### PATCH Version Bump
- Bug fixes
- Minor performance improvements
- Documentation updates
- Dependency updates (non-breaking)
- Test improvements

## Deprecation Policy

### Deprecation Timeline
1. Deprecate feature in MINOR version (warn users)
2. Maintain deprecated feature for at least one MINOR version
3. Remove feature in subsequent MAJOR version
4. Provide migration guidance in deprecation warnings

### Deprecation Warnings
- Python `DeprecationWarning` for programmatic interfaces
- Logging warnings for operational interfaces
- Documentation marks deprecated features
- Migration path clearly documented

## Automation

### Version Tools
- Use standard version bumping tools or manual updates
- CI validates version consistency
- Release process automated where possible

### Changelog Generation
- Encourage manual changelog entries for clarity
- Tooling available for generating from commit messages
- Human review ensures quality and clarity

## Examples

### Version Progression
```
0.1.0 (initial)
0.1.1 (bug fix)
0.2.0 (new Slack integration)
0.2.1 (typo fix in docs)
0.3.0 (added Docker sandbox)
0.3.1 (fixed timeout handling)
1.0.0 (stable release - breaking config change)
1.0.1 (security patch)
1.1.0 (added model training features)
1.1.1 (minor UI fix)
2.0.0 (major architecture update)
```

## Exceptions and Special Cases

### Hotfixes
- Critical fixes may bypass normal release cadence
- Still follow versioning rules (typically PATCH)
- Documented appropriately in changelog

### Experimental Features
- Feature flags for experimental functionality
- May change without version bump if behind flag
- Promoted to stable following SemVer rules

### Internal Versions
- Internal tooling may use different versioning
- Not considered part of public API
- Documented separately if shared externally

## References
- [Semantic Versioning Specification](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [PEP 440](https://peps.python.org/pep-0440/) (Python versioning)
- API versioning best practices