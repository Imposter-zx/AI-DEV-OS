# Security Policy

## Supported Versions

We are currently only supporting security fixes for the `main` branch.

## Reporting a Vulnerability

If you discover a security vulnerability within this project, please do NOT open a public issue. Instead, send an email to security@example.com (replace with real email).

Include as much information as possible:
- A description of the vulnerability.
- Steps to reproduce.
- Potential impact.

We will acknowledge your report within 48 hours and provide a timeline for a fix.

## Critical Protections
- DO NOT commit API keys to this repository. Use environment variables.
- All code must run in sandboxed environments (Modal, Daytona, Docker).
- Review all third-party code before integration.
