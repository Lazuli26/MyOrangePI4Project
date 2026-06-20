# OpenClaw Install Record

## Purpose

This note records the OpenClaw installation performed on the Orange Pi on `2026-06-03`.

## Target

- Host: `orangepi4pro`
- IP: `192.168.50.71`
- User used for install: `orangepi`

## Install Method

- Official installer used: `install-cli.sh`
- Command used:

```bash
curl -fsSL https://openclaw.ai/install-cli.sh | bash -s -- --no-onboard
```

## Installed State

- Installed under: `/home/orangepi/.openclaw`
- Node runtime installed under: `/home/orangepi/.openclaw/tools/node-v22.22.0`
- Wrapper installed at: `/home/orangepi/.openclaw/bin/openclaw`
- Global symlink added at: `/usr/local/bin/openclaw`
- Verified version: `OpenClaw 2026.5.28 (e932160)`

## Verification

Verified over SSH that:

- the installer completed successfully
- `/home/orangepi/.openclaw/bin/openclaw --version` works
- `/usr/local/bin/openclaw` points at the installed wrapper

Example verification commands:

```bash
/home/orangepi/.openclaw/bin/openclaw --version
/usr/local/bin/openclaw --version
```

## Current State

- Onboarding was later completed
- Ollama Cloud was configured as the model provider
- A persistent gateway configuration exists at `/home/orangepi/.openclaw/openclaw.json`
- A user service is present for the gateway under `~/.config/systemd/user/openclaw-gateway.service`

## Model Configuration

As of the latest follow-up:

- Primary model: `ollama/glm-4.7:cloud`
- Fallback 1: `ollama/minimax-m2.1:cloud`
- Fallback 2: `ollama/nemotron-3-super`

Reason for this selection:

- `glm-4.7:cloud` and `minimax-m2.1:cloud` are documented by Ollama as strong coding/tool-use cloud models and are recommended for coding integrations
- Both are suitable for OpenClaw-style agentic workflows with tool calling
- The local `nemotron-3-super` model was retained as a safety fallback

Operational note:

- Live probing against `ollama.com` showed the account currently hitting cloud usage throttling on some accepted models (`429 Too Many Requests`)
- Some larger/newer cloud models returned `403 Forbidden` for this account during direct API probing
- Because of that, the chosen defaults were set to the conservative free-to-start Ollama coding recommendations rather than the newest flagship models

Backup created before model edits:

- `/home/orangepi/.openclaw/openclaw.json.pre-ollama-cloud-models.bak`

## Notes

- This is a low-impact user-space install suitable for the current SD-backed root setup.
- If OpenClaw will be used heavily, monitor storage growth under `/home/orangepi/.openclaw` and any future workspace/state directories.
