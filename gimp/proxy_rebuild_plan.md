# Claude Code Proxy - Rebuild Plan (v2 - A+ Verified)

## Project Overview
The "Claude Code Proxy" is a high-performance middleware system sit between AI CLI tools (Claude Code, Qwen Code, Codex, etc.) and LLM providers. It provides **resilience (cascade/retry)**, **cost-optimization (multi-layer compression)**, and **multi-agent orchestration (Crosstalk)**.

## Core Features to Recreate

### 1. Multi-Layer Compression Chain
- **Headroom (:8787)**: HTTP proxy that intercepts LLM requests. It uses **Hooks** to apply specific context-reduction logic based on the client (OpenClaw, Agno, etc.).
- **RTK (Rust Token Killer)**: A rule-based CLI engine. It uses **Filter Manifests** (`.toml` files) to strip redundant data from common CLI tool outputs (e.g., `ls`, `docker ps`, `terraform plan`) before they are sent to the LLM.
- **Claude Code Proxy (:8082)**: The central hub for routing and metrics.

### 2. Exchange-of-Thought (EoT) Crosstalk
A sophisticated multi-agent orchestration system that allows models to collaborate via 4 paradigms:
- **Memory**: Persistent insight storage.
- **Report**: Structural findings sharing.
- **Relay**: Sequential chain-of-thought.
- **Debate**: Adversarial reasoning with confidence evaluation.

### 3. Intelligent Resilience & Routing
- **Circuit Breaker**: Tracks "Soft Failures" (incomplete JSON, empty choices) and "Hard Failures" (429, 500). State is persisted to survive reboots.
- **Hybrid Cascade**: Combines local sequential retries with OpenRouter's native multi-model fan-out.
- **Intent-Based Routing**: Automatically substitutes models based on task (Background, Think, Image, Web Search, Long Context).

### 4. Management & Monitoring
- **TUI Management**: A Python-based TUI (`crosstalk_studio.py`, `proxies` script) for managing chains and sessions.
- **Web Dashboard**: Svelte 5-based interface for analytics and configuration.
- **Status Integration**: Dynamic injection of compression and health metrics into the Claude Code status bar.
