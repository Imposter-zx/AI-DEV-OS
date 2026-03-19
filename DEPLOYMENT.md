# Deployment Guide

This document describes how to deploy AI Dev OS and configure it for production.

## 1. Cloud Sandboxes

AI Dev OS requires robust isolation for its agents. We recommend Modal for production.
- To configure Modal, run `python scripts/setup-sandboxes.py --provider modal`
- Ensure the `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` environment variables are set.

## 2. Setting Up GitHub Integrations

To automate Pull Requests and webhooks:
- Go to your repository settings and enable Discussions.
- Add branch protection rules on `main` to require approvals.
- Configure Webhooks to point to your AI Dev OS endpoint.

## 3. Supported Providers

- Docker (Local sandbox, good for development)
- Modal (Cloud GPU sandbox, essential for `unsloth` and `newton`)
- Daytona & Runloop (Coming soon)
