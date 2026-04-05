# Dependency Strategy (Phase A)

## Chosen Approach
We'll use the existing `pyproject.toml` configuration with hatchling build system. This provides:
- Reproducible builds and installations
- Integrated dependency management 
- Clear separation of runtime vs dev dependencies
- Compatibility with pip install workflow

## Implementation
Runtime dependencies: Defined in `[project]dependencies`
Development dependencies: Defined in `[dependency-groups]dev`

## Installation Commands
```bash
# Development install
pip install -e ".[dev]"

# Runtime-only install  
pip install -e .
```

## CI/CD Integration
The GitHub Actions workflow uses:
```bash
pip install -e ".[dev]"
```
to install both runtime and development dependencies.

## Notes
- This avoids introducing Poetry while maintaining the benefits of explicit dependency management
- Lock file equivalent can be generated with `pip freeze > requirements.txt` if needed for specific environments
- All existing pyproject.toml configuration is leveraged