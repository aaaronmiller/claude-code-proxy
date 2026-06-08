# Config & Infrastructure file diffs

=== FILE: start_proxy.py ===
--- claude-code-proxy-upstream/start_proxy.py	2026-04-21 15:57:01.097681075 -0700
+++ claude-code-proxy/start_proxy.py	2026-03-13 15:51:17.957991092 -0700
@@ -3,11 +3,410 @@
 
 import sys
 import os
+import argparse
 
 # Add src to Python path
 sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
 
-from src.main import main
+def main():
+    """Parse CLI arguments and start the proxy."""
+    parser = argparse.ArgumentParser(
+        description='Claude Code Proxy - Use Claude API with OpenAI-compatible providers',
+        formatter_class=argparse.RawDescriptionHelpFormatter,
+        epilog="""
+✨ Usage Tips:
+  → All Settings:        %(prog)s --settings
+  → Configure Models:    %(prog)s --select-models
+  → View Analytics:      %(prog)s --analytics
+  → Health Check:        %(prog)s --doctor
+  → Dry Run:             %(prog)s --dry-run
+  
+  → Standard Start:      %(prog)s
+  → Force Setup:         %(prog)s --setup
+
+For more details, see docs/guides/configuration.md
+        """
+    )
+
+    # Create argument groups
+    model_group = parser.add_argument_group('🤖 Model Configuration')
+    reasoning_group = parser.add_argument_group('🧠 Reasoning & Thinking')
+    server_group = parser.add_argument_group('🔌 Server Settings')
+    mode_group = parser.add_argument_group('💾 Profile/Mode Management')
+    crosstalk_group = parser.add_argument_group('🗣️  Crosstalk Orchestration')
+    tools_group = parser.add_argument_group('🛠️  Interactive Tools & Config')
+    validation_group = parser.add_argument_group('✅ Validation & Diagnostics')
+
+    # Model arguments
+    model_group.add_argument('--big-model', dest='big_model', metavar='MODEL',
+                       help='Model for Claude Opus requests')
+    model_group.add_argument('--middle-model', dest='middle_model', metavar='MODEL',
+                       help='Model for Claude Sonnet requests')
+    model_group.add_argument('--small-model', dest='small_model', metavar='MODEL',
+                       help='Model for Claude Haiku requests')
+    model_group.add_argument('--select-models', action='store_true',
+                       help='Launch interactive model selector')
+    model_group.add_argument('--model-cascade', dest='model_cascade', action='store_true',
+                       help='Enable model cascade fallback on provider errors')
+
+    # Reasoning arguments
+    reasoning_group.add_argument('--reasoning-effort', dest='reasoning_effort',
+                       choices=['low', 'medium', 'high'],
+                       help='Reasoning effort level (low, medium, high)')
+    reasoning_group.add_argument('--verbosity', dest='verbosity',
+                       help='Response verbosity level')
+    reasoning_group.add_argument('--reasoning-exclude', dest='reasoning_exclude',
+                       choices=['true', 'false'],
+                       help='Whether to exclude reasoning tokens from response')
+
+    # Server arguments
+    server_group.add_argument('--host', dest='host', metavar='HOST',
+                       help='Server host (default: 0.0.0.0)')
+    server_group.add_argument('--port', dest='port', type=int, metavar='PORT',
+                       help='Server port (default: 8082)')
+    server_group.add_argument('--log-level', dest='log_level',
+                       choices=['debug', 'info', 'warning', 'error', 'critical'],
+                       help='Logging level')
+
+    # Mode arguments
+    mode_group.add_argument('--list-modes', action='store_true',
+                       help='List all saved modes')
+    mode_group.add_argument('--load-mode', dest='load_mode', metavar='ID/NAME',
+                       help='Load a saved mode (ID or name)')
+    mode_group.add_argument('--save-mode', dest='save_mode', metavar='NAME',
+                       help='Save current configuration as a mode')
+    mode_group.add_argument('--delete-mode', dest='delete_mode', metavar='ID/NAME',
+                       help='Delete a saved mode')
+    mode_group.add_argument('--mode', dest='mode_name', metavar='NAME',
+                       help='Shorthand for --save-mode')
+
+    # Crosstalk options
+    crosstalk_group.add_argument('--crosstalk-studio', action='store_true',
+                       help='Launch Crosstalk Studio TUI (visual multi-model chat)')
+    crosstalk_group.add_argument('--crosstalk-init', action='store_true',
+                       help='Launch interactive crosstalk setup wizard')
+    crosstalk_group.add_argument('--crosstalk', dest='crosstalk_models',
+                       help='Quick setup (comma-separated models)')
+    crosstalk_group.add_argument('--system-prompt-big', dest='big_system_prompt',
+                       help='System prompt for BIG model')
+    crosstalk_group.add_argument('--system-prompt-middle', dest='middle_system_prompt',
+                       help='System prompt for MIDDLE model')
+    crosstalk_group.add_argument('--system-prompt-small', dest='small_system_prompt',
+                       help='System prompt for SMALL model')
+    crosstalk_group.add_argument('--crosstalk-iterations', dest='crosstalk_iterations', type=int,
+                       help='Number of iterations (default: 20)')
+    crosstalk_group.add_argument('--crosstalk-topic', dest='crosstalk_topic',
+                       help='Initial topic')
+    crosstalk_group.add_argument('--crosstalk-paradigm', dest='crosstalk_paradigm',
+                       choices=['memory', 'report', 'relay', 'debate'],
+                       help='Communication paradigm')
+
+    # Interactive Tools
+    tools_group.add_argument('--setup', action='store_true',
+                       help='Launch first-time setup wizard')
+    tools_group.add_argument('--configure-prompts', action='store_true',
+                       help='Launch prompt injection configurator')
+    tools_group.add_argument('--configure-terminal', action='store_true',
+                       help='Launch terminal output configurator')
+    tools_group.add_argument('--configure-dashboard', action='store_true',
+                       help='Launch dashboard module configurator')
+    tools_group.add_argument('--analytics', action='store_true',
+                       help='View usage analytics')
+    tools_group.add_argument('--settings', action='store_true',
+                       help='Launch unified settings TUI (models, terminal, dashboard, prompts)')
+    tools_group.add_argument('--doctor', action='store_true',
+                       help='Run health check and auto-fix common issues')

=== FILE: pyproject.toml ===
--- claude-code-proxy-upstream/pyproject.toml	2026-04-21 15:57:01.094197312 -0700
+++ claude-code-proxy/pyproject.toml	2026-04-02 14:54:53.648966352 -0700
@@ -15,26 +15,36 @@
     "Intended Audience :: Developers",
     "License :: OSI Approved :: MIT License",
     "Programming Language :: Python :: 3",
-    "Programming Language :: Python :: 3.8",
-    "Programming Language :: Python :: 3.9",
     "Programming Language :: Python :: 3.10",
     "Programming Language :: Python :: 3.11",
     "Programming Language :: Python :: 3.12",
 ]
-requires-python = ">=3.9"
+requires-python = ">=3.10"
 dependencies = [
-    "fastapi[standard]>=0.115.11",
-    "uvicorn>=0.34.0",
-    "pydantic>=2.0.0",
-    "python-dotenv>=1.0.0",
-    "openai>=1.54.0",
+    "fastapi[standard]>=0.121.0",
+    "uvicorn>=0.38.0",
+    "pydantic>=2.12.0",
+    "python-dotenv>=1.2.0",
+    "openai>=2.8.0",
+    "rich>=14.2.0",
+    "tiktoken>=0.12.0",
+    "questionary>=2.0.0",
+    "readchar>=4.0.0",
+    "psutil>=7.0.0",
+    "aiohttp>=3.11.0",
+    "httpx>=0.28.0",
+    "numpy>=2.0.0",
+    "openpyxl>=3.1.0",
+    "reportlab>=4.0.0",
+    "requests>=2.32.0",
 ]
 
 [project.optional-dependencies]
 dev = [
-    "pytest>=7.0.0",
-    "pytest-asyncio>=0.21.0",
-    "httpx>=0.25.0",
+    "pytest>=8.0.0",
+    "pytest-asyncio>=0.24.0",
+    "pytest-cov>=6.0.0",
+    "httpx>=0.28.0",
 ]
 
 [project.urls]
@@ -45,13 +55,14 @@
 [project.scripts]
 claude-code-proxy = "src.main:main"
 
-[tool.uv]
-dev-dependencies = [
-    "pytest>=7.0.0",
-    "pytest-asyncio>=0.21.0",
-    "black>=23.0.0",
-    "isort>=5.12.0",
-    "mypy>=1.0.0",
+[dependency-groups]
+dev = [
+    "pytest>=8.0.0",
+    "pytest-asyncio>=0.24.0",
+    "pytest-cov>=6.0.0",
+    "black>=25.0.0",
+    "isort>=5.13.0",
+    "mypy>=1.15.0",
     "pyinstaller>=6.15.0",
 ]
 
@@ -71,3 +82,10 @@
 warn_return_any = true
 warn_unused_configs = true
 disallow_untyped_defs = true
+
+[tool.pytest.ini_options]
+asyncio_mode = "auto"
+asyncio_default_fixture_loop_scope = "function"
+markers = [
+    "integration: marks tests as integration tests (require running server)",
+]

=== FILE: requirements.txt ===
--- claude-code-proxy-upstream/requirements.txt	2026-04-21 15:57:01.094197312 -0700
+++ claude-code-proxy/requirements.txt	2026-04-21 15:30:56.785971286 -0700
@@ -1,12 +1,300 @@
-fastapi[standard]>=0.115.11
-uvicorn>=0.34.0
-pydantic>=2.0.0
-python-dotenv>=1.0.0
-openai>=1.54.0
-# Dev dependencies
-pytest>=7.0.0
-pytest-asyncio>=0.21.0
-httpx>=0.25.0
-black>=23.0.0
-isort>=5.12.0
-mypy>=1.0.0
\ No newline at end of file
+# This file was autogenerated by uv via the following command:
+#    uv export --no-hashes
+-e .
+aiohappyeyeballs==2.6.1
+    # via aiohttp
+aiohttp==3.13.5
+    # via claude-code-proxy
+aiosignal==1.4.0
+    # via aiohttp
+altgraph==0.17.5
+    # via
+    #   macholib
+    #   pyinstaller
+annotated-doc==0.0.4
+    # via
+    #   fastapi
+    #   typer
+annotated-types==0.7.0
+    # via pydantic
+anyio==4.13.0
+    # via
+    #   httpx
+    #   openai
+    #   starlette
+    #   watchfiles
+async-timeout==5.0.1 ; python_full_version < '3.11'
+    # via aiohttp
+attrs==26.1.0
+    # via aiohttp
+backports-asyncio-runner==1.2.0 ; python_full_version < '3.11'
+    # via pytest-asyncio
+black==26.3.1
+certifi==2026.2.25
+    # via
+    #   httpcore
+    #   httpx
+    #   requests
+    #   sentry-sdk
+charset-normalizer==3.4.6
+    # via
+    #   reportlab
+    #   requests
+click==8.3.1
+    # via
+    #   black
+    #   rich-toolkit
+    #   typer
+    #   uvicorn
+colorama==0.4.6 ; sys_platform == 'win32'
+    # via
+    #   click
+    #   pytest
+    #   tqdm
+    #   uvicorn
+coverage==7.13.5
+    # via pytest-cov
+distro==1.9.0
+    # via openai
+dnspython==2.8.0
+    # via email-validator
+email-validator==2.3.0
+    # via
+    #   fastapi
+    #   pydantic
+et-xmlfile==2.0.0
+    # via openpyxl
+exceptiongroup==1.3.1 ; python_full_version < '3.11'
+    # via
+    #   anyio
+    #   pytest
+fastapi==0.135.2
+    # via claude-code-proxy
+fastapi-cli==0.0.24
+    # via fastapi
+fastapi-cloud-cli==0.15.1
+    # via fastapi-cli
+fastar==0.9.0
+    # via fastapi-cloud-cli
+frozenlist==1.8.0
+    # via
+    #   aiohttp
+    #   aiosignal
+h11==0.16.0
+    # via
+    #   httpcore
+    #   uvicorn
+httpcore==1.0.9
+    # via httpx
+httptools==0.7.1
+    # via uvicorn
+httpx==0.28.1
+    # via
+    #   claude-code-proxy
+    #   fastapi
+    #   fastapi-cloud-cli
+    #   openai
+idna==3.11
+    # via
+    #   anyio
+    #   email-validator
+    #   httpx
+    #   requests
+    #   yarl
+iniconfig==2.3.0

=== FILE: .env.example ===
--- claude-code-proxy-upstream/.env.example	2026-04-21 15:57:01.079590010 -0700
+++ claude-code-proxy/.env.example	2026-03-30 18:22:44.099971483 -0700
@@ -1,64 +1,108 @@
-# Required: Your OpenAI API key
-OPENAI_API_KEY="sk-your-openai-api-key-here"
-
-# Optional: Expected Anthropic API key for client validation
-# If set, clients must provide this exact API key to access the proxy
-ANTHROPIC_API_KEY="your-expected-anthropic-api-key"
-
-# Optional: OpenAI API base URL (default: https://api.openai.com/v1)
-# You can change this to use other providers like Azure OpenAI, local models, etc.
-OPENAI_BASE_URL="https://api.openai.com/v1"
-
-# Optional: Model mappings (BIG and SMALL models)
-BIG_MODEL="gpt-4o"
-# Used for Claude opus requests
-MIDDLE_MODEL="gpt-4o"
-# Used for Claude sonnet requests
-SMALL_MODEL="gpt-4o-mini"    
-# Used for Claude haiku requests
-
-# Optional: Server settings
-HOST="0.0.0.0"
-PORT="8082"
-LOG_LEVEL="INFO"  
-# DEBUG, INFO, WARNING, ERROR, CRITICAL
-
-# Optional: Performance settings  
-MAX_TOKENS_LIMIT="4096"
-# Minimum tokens limit for requests (to avoid errors with thinking model)
-MIN_TOKENS_LIMIT="4096"
-REQUEST_TIMEOUT="90"
-MAX_RETRIES="2"
-
-# Examples for other providers:
-
-# For Azure OpenAI (recommended if OpenAI is not available in your region):
-# OPENAI_API_KEY="your-azure-api-key"
-# OPENAI_BASE_URL="https://your-resource-name.openai.azure.com/openai/deployments/your-deployment-name"
-# AZURE_API_VERSION="2024-03-01-preview"
-# BIG_MODEL="gpt-4"
-# MIDDLE_MODEL="gpt-4"
-# SMALL_MODEL="gpt-35-turbo"
-
-# For local models (like Ollama):
-# OPENAI_API_KEY="dummy-key"  # Required but can be any value for local models
-# OPENAI_BASE_URL="http://localhost:11434/v1"
-# BIG_MODEL="llama3.1:70b"
-# MIDDLE_MODEL="llama3.1:70b"
-# SMALL_MODEL="llama3.1:8b"
-
-# Note: If you get "unsupported_country_region_territory" errors,
-# consider using Azure OpenAI or a local model setup instead.
-
-
-# Custom Headers Configuration
-# Format: HEADER_KEY=header_value
-# These headers will be automatically included in API requests
-# Uncomment the lines below to use custom headers:
-# CUSTOM_HEADER_ACCEPT="application/jsonstream"
-# CUSTOM_HEADER_CONTENT_TYPE="application/json"
-# CUSTOM_HEADER_USER_AGENT="node-fetch"
-# CUSTOM_HEADER_HOST="example.com"
-# CUSTOM_HEADER_AUTHORIZATION="Bearer your-token"
-# CUSTOM_HEADER_X_API_KEY="your-api-key"
-# CUSTOM_HEADER_X_CLIENT_ID="your-client-id"
+# ═══════════════════════════════════════════════════════════════════════════════
+# CLAUDE CODE PROXY - ENVIRONMENT CONFIGURATION
+# ═══════════════════════════════════════════════════════════════════════════════
+# Copy this file to .env and fill in your values
+
+# ─────────────────────────────────────────────────────────────────────────────
+# PRIMARY PROVIDER (Required)
+# ─────────────────────────────────────────────────────────────────────────────
+# OpenRouter (recommended for multi-model access)
+OPENROUTER_API_KEY=sk-or-v1-your-key-here
+
+# Or use a specific provider:
+# OPENAI_API_KEY=sk-your-key-here
+# ANTHROPIC_API_KEY=sk-ant-your-key-here
+
+# Provider endpoint (auto-detected from key if not set)
+# OPENAI_BASE_URL=https://openrouter.ai/api/v1
+
+# ─────────────────────────────────────────────────────────────────────────────
+# MODEL CONFIGURATION
+# ─────────────────────────────────────────────────────────────────────────────
+# Default models for each tier
+BIG_MODEL=anthropic/claude-sonnet-4-20250514
+MIDDLE_MODEL=google/gemini-2.0-flash-001
+SMALL_MODEL=google/gemini-2.0-flash-001
+
+# ─────────────────────────────────────────────────────────────────────────────
+# MODEL CASCADE (Automatic fallback on errors)
+# ─────────────────────────────────────────────────────────────────────────────
+# Enable cascade: tries fallback models on SSL/connection/rate errors
+# MODEL_CASCADE=true
+
+# Comma-separated fallback models (provider/model format)
+# BIG_CASCADE=openai/gpt-4o,anthropic/claude-3-opus,google/gemini-pro
+# MIDDLE_CASCADE=openai/gpt-4o-mini,anthropic/claude-3-sonnet
+# SMALL_CASCADE=openai/gpt-4o-mini,google/gemini-flash
+
+# ─────────────────────────────────────────────────────────────────────────────
+# PER-ENDPOINT OVERRIDES (Optional)
+# ─────────────────────────────────────────────────────────────────────────────
+# Enable per-model endpoints for routing to different providers
+# ENABLE_BIG_ENDPOINT=true
+# BIG_ENDPOINT=http://127.0.0.1:8317/v1
+# BIG_API_KEY=your-vibeproxy-key
+
+# ENABLE_MIDDLE_ENDPOINT=true
+# MIDDLE_ENDPOINT=https://openrouter.ai/api/v1
+# MIDDLE_API_KEY=sk-or-v1-your-key
+
+# ENABLE_SMALL_ENDPOINT=true
+# SMALL_ENDPOINT=https://openrouter.ai/api/v1
+# SMALL_API_KEY=sk-or-v1-your-key
+

=== FILE: README.md ===
--- claude-code-proxy-upstream/README.md	2026-04-21 15:57:01.080197234 -0700
+++ claude-code-proxy/README.md	2026-04-03 23:02:32.161267206 -0700
@@ -1,289 +1,312 @@
-# Claude Code Proxy
+<div align="center">
 
-A proxy server that enables **Claude Code** to work with OpenAI-compatible API providers. Convert Claude API requests to OpenAI API calls, allowing you to use various LLM providers through the Claude Code CLI.
+<img src="web-ui/static/logo.png" alt="The Ultimate Proxy" width="120">
 
-![Claude Code Proxy](demo.png)
+# ⚡ The Ultimate Proxy
 
-## Features
+**The only proxy you need for Claude Code CLI**
 
-- **Full Claude API Compatibility**: Complete `/v1/messages` endpoint support
-- **Multiple Provider Support**: OpenAI, Azure OpenAI, local models (Ollama), and any OpenAI-compatible API
-- **Smart Model Mapping**: Configure BIG and SMALL models via environment variables
-- **Function Calling**: Complete tool use support with proper conversion
-- **Streaming Responses**: Real-time SSE streaming support
-- **Image Support**: Base64 encoded image input
-- **Custom Headers**: Automatic injection of custom HTTP headers for API requests
-- **Error Handling**: Comprehensive error handling and logging
+[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
+[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
+[![2025 Ready](https://img.shields.io/badge/2025-Ready-06ffd4.svg)](#)
 
-## Quick Start
+[Quick Start](#-quick-start) • [Features](#-features) • [Web Dashboard](#-web-dashboard) • [Crosstalk](docs/crosstalk.md) • [Compression Stack](#-compression-stack) • [Roadmap](ROADMAP.md) • [Changelog](changelog.md)
 
-### 1. Install Dependencies
+<br>
 
-```bash
-# Using UV (recommended)
-uv sync
+<img src="web-ui/static/hero-banner.png" alt="The Ultimate Proxy Dashboard" width="800">
 
-# Or using pip
-pip install -r requirements.txt
-```
+**Route Claude Code to any provider. Save 90% on API costs. Run locally for free.**
 
-### 2. Configure
+</div>
+
+---
+
+## 🌟 What Is It?
+
+The Ultimate Proxy sits between Claude Code CLI and your chosen API provider. It translates Anthropic's API format to OpenAI-compatible format, letting you use **any model** with Claude Code:
 
-```bash
-cp .env.example .env
-# Edit .env and add your API configuration
-# Note: Environment variables are automatically loaded from .env file
+```
+Claude Code CLI  →  The Ultimate Proxy  →  Any Provider
+                                           ├─ OpenRouter
+                                           ├─ Gemini / VibeProxy
+                                           ├─ OpenAI
+                                           ├─ Azure
+                                           ├─ Ollama (local)
+                                           └─ LM Studio (local)
 ```
 
-### 3. Start Server
+---
 
-```bash
-# Direct run
-python start_proxy.py
+## 🚀 Quick Start
+
+### Option 1: Unified Installation (Recommended)
 
-# Or with UV
-uv run claude-code-proxy
+**Single command installs everything with automatic GPU detection:**
 
-# Or with docker compose
-docker compose up -d
+```bash
+curl -fsSL https://raw.githubusercontent.com/aaaronmiller/claude-code-proxy/main/install-all.sh | bash
 ```
 
-### 4. Use with Claude Code
+The installer will:
+- 🔍 **Auto-detect your GPU** (NVIDIA CUDA, Intel Arc/iGPU, AMD ROCm, or CPU-only)
+- 💬 **Prompt you to confirm or override** the detected GPU backend
+- ✅ Clone claude-code-proxy
+- ✅ Install Headroom (compression layer)
+- ✅ Install RTK (command compression)
+- ✅ Install GPU compute stack (Level Zero for Intel, CUDA for NVIDIA, ROCm for AMD)
+- ✅ Configure environment variables (`ONEAPI_DEVICE_SELECTOR`, `CUDA_VISIBLE_DEVICES`, etc.)
+- ✅ Add compression aliases (`cc`, `qw`, `qw-resume`)
+- ✅ Start all services
+- ✅ Show health status
 
-```bash
-# If ANTHROPIC_API_KEY is not set in the proxy:
-ANTHROPIC_BASE_URL=http://localhost:8082 ANTHROPIC_API_KEY="any-value" claude
+**Supported GPU backends:**
 
-# If ANTHROPIC_API_KEY is set in the proxy:
-ANTHROPIC_BASE_URL=http://localhost:8082 ANTHROPIC_API_KEY="exact-matching-key" claude
-```
+| Backend | Hardware | Env Vars Set |
+|---------|----------|-------------|
+| **NVIDIA CUDA** | RTX 30/40/50 series, datacenter GPUs | `CUDA_VISIBLE_DEVICES=0` |
+| **Intel Arc / iGPU** | Arc A370M/A580/A770, Iris Xe, UHD | `ONEAPI_DEVICE_SELECTOR=level_zero:0`, `LIBVA_DRIVER_NAME=iHD` |
+| **AMD ROCm** | RX 6000/7000, Instinct MI series | `HSA_OVERRIDE_GFX_VERSION=10.3.0` |
+| **CPU-only** | No GPU available | `HEADROOM_DEVICE=cpu` |
 
-## Configuration
+**Manual installation:**
 
-The application automatically loads environment variables from a `.env` file in the project root using `python-dotenv`. You can also set environment variables directly in your shell.
+```bash
+# Clone & install

=== FILE: CLAUDE.md ===
--- claude-code-proxy-upstream/CLAUDE.md	2026-04-21 15:57:01.080197234 -0700
+++ claude-code-proxy/CLAUDE.md	2026-04-21 15:30:56.779231008 -0700
@@ -1,127 +1,133 @@
-# Claude Code: Best Practices for Effective Collaboration
-
-This document outlines best practices for working with Claude Code to ensure efficient and successful software development tasks.
-
-## Task Management
-
-For complex or multi-step tasks, Claude Code will use:
-*   **TodoWrite**: To create a structured task list, breaking down the work into manageable steps. This provides clarity on the plan and allows for tracking progress.
-*   **TodoRead**: To review the current list of tasks and their status, ensuring alignment and that all objectives are being addressed.
-
-## File Handling and Reading
-
-Understanding file content is crucial before making modifications.
-
-1.  **Targeted Information Retrieval**:
-    *   When searching for specific content, patterns, or definitions within a codebase, prefer using search tools like `Grep` or `Task` (with a focused search prompt). This is more efficient than reading entire files.
-
-2.  **Reading File Content**:
-    *   **Small to Medium Files**: For files where full context is needed or that are not excessively large, the `Read` tool can be used to retrieve the entire content.
-    *   **Large File Strategy**:
-        1.  **Assess Size**: Before reading a potentially large file, its size should be determined (e.g., using `ls -l` via the `Bash` tool or by an initial `Read` with a small `limit` to observe if content is truncated).
-        2.  **Chunked Reading**: If a file is large (e.g., over a few thousand lines), it should be read in manageable chunks (e.g., 1000-2000 lines at a time) using the `offset` and `limit` parameters of the `Read` tool. This ensures all content can be processed without issues.
-    *   Always ensure that the file path provided to `Read` is absolute.
-
-## File Editing
-
-Precision is key for successful file edits. The following strategies lead to reliable modifications:
-
-1.  **Pre-Edit Read**: **Always** use the `Read` tool to fetch the content of the file *immediately before* attempting any `Edit` or `MultiEdit` operation. This ensures modifications are based on the absolute latest version of the file.
-
-2.  **Constructing `old_string` (The text to be replaced)**:
-    *   **Exact Match**: The `old_string` must be an *exact* character-for-character match of the segment in the file you intend to replace. This includes all whitespace (spaces, tabs, newlines) and special characters.
-    *   **No Read Artifacts**: Crucially, do *not* include any formatting artifacts from the `Read` tool's output (e.g., `cat -n` style line numbers or display-only leading tabs) in the `old_string`. It must only contain the literal characters as they exist in the raw file.
-    *   **Sufficient Context & Uniqueness**: Provide enough context (surrounding lines) in `old_string` to make it uniquely identifiable at the intended edit location. The "Anchor on a Known Good Line" strategy is preferred: `old_string` is a larger, unique block of text surrounding the change or insertion point. This is highly reliable.
-
-3.  **Constructing `new_string` (The replacement text)**:
-    *   **Exact Representation**: The `new_string` must accurately represent the desired state of the code, including correct indentation, whitespace, and newlines.
-    *   **No Read Artifacts**: As with `old_string`, ensure `new_string` does *not* contain any `Read` tool output artifacts.
-
-4.  **Choosing the Right Editing Tool**:
-    *   **`Edit` Tool**: Suitable for a single, well-defined replacement in a file.
-    *   **`MultiEdit` Tool**: Preferred when multiple changes are needed within the same file. Edits are applied sequentially, with each subsequent edit operating on the result of the previous one. This tool is highly effective for complex modifications.
-
-5.  **Verification**:
-    *   The success confirmation from the `Edit` or `MultiEdit` tool (especially if `expected_replacements` is used and matches) is the primary indicator that the change was made.
-    *   If further visual confirmation is needed, use the `Read` tool with `offset` and `limit` parameters to view only the specific section of the file that was changed, rather than re-reading the entire file.
-
-### Reliable Code Insertion with MultiEdit
-
-When inserting larger blocks of new code (e.g., multiple functions or methods) where a simple `old_string` might be fragile due to surrounding code, the following `MultiEdit` strategy can be more robust:
-
-1.  **First Edit - Targeted Insertion Point**: For the primary code block you want to insert (e.g., new methods within a class), identify a short, unique, and stable line of code immediately *after* your desired insertion point. Use this stable line as the `old_string`.
-    *   The `new_string` will consist of your new block of code, followed by a newline, and then the original `old_string` (the stable line you matched on).
-    *   Example: If inserting methods into a class, the `old_string` might be the closing brace `}` of the class, or a comment that directly follows the class.
-
-2.  **Second Edit (Optional) - Ancillary Code**: If there's another, smaller piece of related code to insert (e.g., a function call within an existing method, or an import statement), perform this as a separate, more straightforward edit within the `MultiEdit` call. This edit usually has a more clearly defined and less ambiguous `old_string`.
-
-**Rationale**:
-*   By anchoring the main insertion on a very stable, unique line *after* the insertion point and prepending the new code to it, you reduce the risk of `old_string` mismatches caused by subtle variations in the code *before* the insertion point.
-*   Keeping ancillary edits separate allows them to succeed even if the main insertion point is complex, as they often target simpler, more reliable `old_string` patterns.
-*   This approach leverages `MultiEdit`'s sequential application of changes effectively.
-
-**Example Scenario**: Adding new methods to a class and a call to one of these new methods elsewhere.
-*   **Edit 1**: Insert the new methods. `old_string` is the class's closing brace `}`. `new_string` is `
-    [new methods code]
-    }`.
-*   **Edit 2**: Insert the call to a new method. `old_string` is `// existing line before call`. `new_string` is `// existing line before call
-    this.newMethodCall();`.
-
-This method provides a balance between precise editing and handling larger code insertions reliably when direct `old_string` matches for the entire new block are problematic.
-
-## Handling Large Files for Incremental Refactoring
-
-When refactoring large files incrementally rather than rewriting them completely:
-
-1. **Initial Exploration and Planning**:
-   * Begin with targeted searches using `Grep` to locate specific patterns or sections within the file.
-   * Use `Bash` commands like `grep -n "pattern" file` to find line numbers for specific areas of interest.
-   * Create a clear mental model of the file structure before proceeding with edits.
-
-2. **Chunked Reading for Large Files**:
-   * For files too large to read at once, use multiple `Read` operations with different `offset` and `limit` parameters.
-   * Read sequential chunks to build a complete understanding of the file.
-   * Use `Grep` to pinpoint key sections, then read just those sections with targeted `offset` parameters.
-
-3. **Finding Key Implementation Sections**:
-   * Use `Bash` commands with `grep -A N` (to show N lines after a match) or `grep -B N` (to show N lines before) to locate function or method implementations.
-   * Example: `grep -n "function findTagBoundaries" -A 20 filename.js` to see the first 20 lines of a function.
-
-4. **Pattern-Based Replacement Strategy**:
-   * Identify common patterns that need to be replaced across the file.
-   * Use the `Bash` tool with `sed` for quick previews of potential replacements.
-   * Example: `sed -n "s/oldPattern/newPattern/gp" filename.js` to preview changes without making them.
-
-5. **Sequential Selective Edits**:
-   * Target specific sections or patterns one at a time rather than attempting a complete rewrite.
-   * Focus on clearest/simplest cases first to establish a pattern of successful edits.
-   * Use `Edit` for well-defined single changes within the file.
-
-6. **Batch Similar Changes Together**:
-   * Group similar types of changes (e.g., all references to a particular function or variable).
-   * Use `Bash` with `sed` to preview the scope of batch changes: `grep -n "pattern" filename.js | wc -l`
-   * For systematic changes across a file, consider using `sed` through the `Bash` tool: `sed -i "s/oldPattern/newPattern/g" filename.js`
-
-7. **Incremental Verification**:
-   * After each set of changes, verify the specific sections that were modified.
-   * For critical components, read the surrounding context to ensure the changes integrate correctly.
-   * Validate that each change maintains the file's structure and logic before proceeding to the next.
-
-8. **Progress Tracking for Large Refactors**:
-   * Use the `TodoWrite` tool to track which sections or patterns have been updated.
-   * Create a checklist of all required changes and mark them off as they're completed.
-   * Record any sections that require special attention or that couldn't be automatically refactored.
-
-## Commit Messages
-
-When Claude Code generates commit messages on your behalf:
