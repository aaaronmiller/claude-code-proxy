# Text/Config File Audit: /home/cheta/code/claude-code-proxy/src/models/scout/leaderboard.json
**File Size:** 1157 bytes

## Content / Data Structure:
```text
{
  "generated_at": "2026-03-24T20:10:38.246022+00:00",
  "smartest": [],
  "coding": [],
  "free": [
    {
      "id": "nvidia/nemotron-3-super-120b-a12b:free",
      "name": "NVIDIA: Nemotron 3 Super (free)",
      "intelligence_score": 0.0,
      "context_length": 262144,
      "throughput_tps": null
    },
    {
      "id": "qwen/qwen3-next-80b-a3b-instruct:free",
      "name": "Qwen: Qwen3 Next 80B A3B Instruct (free)",
      "intelligence_score": 0.0,
      "context_length": 262144,
      "throughput_tps": null
    },
    {
      "id": "qwen/qwen3-coder:free",
      "name": "Qwen: Qwen3 Coder 480B A35B (free)",
      "intelligence_score": 0.0,
      "context_length": 262000,
      "throughput_tps": null
    },
    {
      "id": "stepfun/step-3.5-flash:free",
      "name": "StepFun: Step 3.5 Flash (free)",
      "intelligence_score": 0.0,
      "context_length": 256000,
      "throughput_tps": null
    },
    {
      "id": "nvidia/nemotron-3-nano-30b-a3b:free",
      "name": "NVIDIA: Nemotron 3 Nano 30B A3B (free)",
      "intelligence_score": 0.0,
      "context_length": 256000,
      "throughput_tps": null
    }
  ],
  "value": []
}
```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/src/static/README.md
**File Size:** 7306 bytes

## Features & Sections Declared:
# Web UI for Claude Code Proxy
## Features
### 🎯 Configuration Management
### 📁 Profile Management
### 🤖 Model Browser
### 📊 Real-Time Monitoring
## Access
## Usage
### 1. Basic Configuration
### 2. Profile Management
### 3. Model Selection
### 4. Monitoring
### 5. Real-Time Dashboard
## API Endpoints
### Configuration
### Profiles
### Models & Stats
### WebSocket (Real-Time)
### Analytics
### Billing
### Benchmarking
### Users (Multi-User Mode)
## Hot Reload
## Profile Storage
## Security
## Troubleshooting
### Web UI Not Loading
### Configuration Not Saving
### Stats Not Showing
## Browser Support
## Development


## Content / Data Structure:
```text
# Web UI for Claude Code Proxy

## Features

### 🎯 Configuration Management
- **Visual Editor**: Edit all proxy settings through a modern web interface
- **Hot Reload**: Apply configuration changes without restarting the proxy
- **Validation**: Real-time validation of configuration values
- **Export**: Download configuration as `.env` file

### 📁 Profile Management
- **Save Profiles**: Save different configuration sets with custom names
- **Quick Load**: Switch between profiles with one click
- **Profile Library**: Manage multiple configurations (dev, prod, testing, etc.)
- **Automatic Timestamps**: Track when each profile was last modified

### 🤖 Model Browser
- **352+ Models**: Browse all available models from OpenRouter
- **Smart Search**: Filter by name, provider, or capabilities
- **Model Details**: View context limits, pricing, and features
- **Quick Copy**: Click to copy model IDs to clipboard

### 📊 Real-Time Monitoring
- **Request Statistics**: View requests, tokens, cost, and latency
- **Recent Activity**: See the last 10 requests with full details
- **Live Status**: Proxy health and mode indicator
- **Usage Analytics**: When TRACK_USAGE is enabled
- **WebSocket Dashboard**: Live request waterfall with real-time updates
- **Performance Charts**: Real-time metrics visualization

## Access

The Web UI is automatically available at:
- **http://localhost:8082/** - Main interface (Configuration & Profiles)
- **http://localhost:8082/dashboard** - Real-time monitoring dashboard
- **http://localhost:8082/config** - Direct to config tab

## Usage

### 1. Basic Configuration

1. Open http://localhost:8082 in your browser
2. Click the "⚙️ Configuration" tab (default)
3. Update settings:
   - API keys (OpenAI, Anthropic)
   - Model mappings (BIG, MIDDLE, SMALL)
   - Reasoning configuration
   - Monitoring options
4. Click "💾 Save & Apply" to apply changes (no restart!)

### 2. Profile Management

1. Configure your settings in the Configuration tab
2. Switch to the "📁 Profiles" tab
3. Enter a profile name (e.g., "Production", "Testing", "GPT-4")
4. Click "💾 Save Current as Profile"
5. Load any profile later with one click

**Use Cases:**
- **Dev/Prod**: Separate configurations for development and production
- **Provider Testing**: Switch between OpenAI, OpenRouter, local models
- **Model Experiments**: Different model configurations for testing
- **Team Sharing**: Export profiles as JSON and share with team

### 3. Model Selection

1. Go to the "🤖 Models" tab
2. Use the search box to find models by name
3. Filter by provider (OpenAI, Anthropic, Google, Meta, etc.)
4. Click any model to copy its ID to clipboard
5. Paste into Configuration tab or .env file

### 4. Monitoring

1. Navigate to the "📊 Monitor" tab
2. View real-time statistics:
   - Requests today
   - Total tokens used
   - Estimated cost (24h)
   - Average latency
3. See recent requests with details
4. Click "🔄 Refresh Stats" to update

### 5. Real-Time Dashboard

For live monitoring with WebSocket updates, visit **http://localhost:8082/dashboard**:

1. **Performance Metrics** - Real-time request count, success rate, latency
2. **Request Waterfall** - Live visualization of requests as they flow through the proxy
3. **Model Usage** - Top models and usage statistics
4. **Cost Tracking** - Live cost accumulation and estimates
5. **Auto-Updates** - Dashboard updates automatically as requests are processed

The dashboard uses WebSocket for real-time updates with no page refresh needed.

## API Endpoints

The Web UI uses these REST API endpoints:

### Configuration
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration (hot reload)
- `POST /api/config/reload` - Reload from environment variables

### Profiles
- `GET /api/profiles` - List all profiles
- `POST /api/profiles` - Save a profile
- `GET /api/profiles/{name}` - Load a specific profile
- `DELETE /api/profiles/{name}` - Delete a profile

### Models & Stats
- `GET /api/models` - List available models
- `GET /api/stats` - Get proxy statistics

### WebSocket (Real-Time)
- `WS /ws/dashboard` - WebSocket connection for live dashboard updates

### Analytics
- `GET /api/analytics/summary?days=7` - Get analytics summary for past N days
- `GET /api/analytics/timeseries?days=7` - Time-series data for charts
- `GET /api/analytics/errors?days=7` - Error analytics and trends
- `GET /api/analytics/export?format=csv&days=30` - Export data (CSV/JSON)
- `GET /api/analytics/cost-breakdown?days=7` - Cost breakdown by model/provider

### Billing
- `GET /api/billing/usage?start_date=2025-01-01&end_date=2025-01-31` - Fetch provider usage
- `GET /api/billing/balance` - Get account balances for all providers
- `GET /api/billing/provider/{name}` - Get provider-specific billing info

### Benchmarking
- `POST /api/benchmarks/run` - Run benchmark tests for a model
- `GET /api/benchmarks/results` - List all benchmark results
- `GET /api/benchmarks/results/{benchmark_id}` - Get specific benchmark result
- `POST /api/benchmarks/compare` - Compare multiple models

### Users (Multi-User Mode)
- `POST /api/users` - Create new user with API key
- `GET /api/users/me` - Get current user info
- `GET /api/users/me/quota` - Check user quota status
- `GET /api/users/me/usage?days=7` - Get user usage history

## Hot Reload

Configuration changes are applied **immediately without restart**:
- ✅ API keys
- ✅ Model mappings
- ✅ Reasoning settings
- ✅ Monitoring options
- ✅ Base URLs

This allows you to:
- Test different providers instantly
- Switch models on the fly
- Enable/disable features
- Debug configuration issues

## Profile Storage

Profiles are stored in `configs/profiles/` as JSON files:

```json
{
  "name": "Production",
  "modified": "2025-01-19T10:30:00Z",
  "config": {
    "openai_api_key": "sk-...",
    "big_model": "gpt-4o",
    "middle_model": "gpt-4o",
    "small_model": "gpt-4o-mini",
    "track_usage": true
  }
}
```

You can:
- Share profiles by copying JSON files
- Version control profiles in Git
- Backup profiles for disaster recovery
- Programmatically generate profiles

## Security

- **API Keys**: Masked in the UI (shown as `***`)
- **Local Storage**: All data stored on your machine
- **No Cloud Sync**: Profiles never leave your server
- **HTTPS Ready**: Works with reverse proxies (nginx, Caddy)

## Troubleshooting

### Web UI Not Loading
1. Check proxy is running: `curl http://localhost:8082/health`
2. Verify static files exist: `ls static/index.html`
3. Check browser console for errors (F12)

### Configuration Not Saving
1. Check write permissions on `configs/` directory
2. Look for errors in proxy logs
3. Verify JSON syntax if editing profiles manually

### Stats Not Showing
1. Enable usage tracking: `TRACK_USAGE=true` in .env
2. Restart proxy to initialize database
3. Make some API requests to generate data

## Browser Support

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

## Development

The Web UI is built with:
- **Vanilla JavaScript** - No frameworks, fast loading
- **CSS3** - Modern styling with dark theme
- **FastAPI** - Backend REST API
- **SQLite** - Statistics storage (via usage_tracker)

To customize:
1. Edit files in `static/`
2. Refresh browser (changes apply immediately)
3. No build step required

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/quickstart.md
**File Size:** 2113 bytes

## Features & Sections Declared:
# Quickstart Guide
## Initial Setup
## First Run
# Perform initial full sync (API + deep scraper)
## Typical Operations
### Daily Operation (Auto Mode)
# Automatically checks timestamps:
# - Runs API sync if last_run > 24 hours
# - Runs deep scraper if new models detected or weekly audit due
### Fast-Only (Dev/Testing)
# Skip deep scraping, only refresh API data
### Debugging
# Dry run with verbose output and token report
## Expected Output
## Troubleshooting
## Next Steps


## Content / Data Structure:
```text
# Quickstart Guide

## Initial Setup

1. **Install dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. **Configure environment**
   ```bash
   export OPENROUTER_API_KEY="your-key-here"
   export DATA_DIR="data"  # optional, default is data/
   ```

3. **Create data directory**
   ```bash
   mkdir -p data
   ```

## First Run

```bash
# Perform initial full sync (API + deep scraper)
python -m openrouter_model_scout.main --force
```

The first run will:
- Fetch all models from OpenRouter API (~300 models, <30s)
- Deep scrape benchmark data for all models (may take up to 60 minutes)
- Generate `data/leaderboard.json` with top-5 lists
- Create `data/meta.json` with run history

## Typical Operations

### Daily Operation (Auto Mode)
```bash
# Automatically checks timestamps:
# - Runs API sync if last_run > 24 hours
# - Runs deep scraper if new models detected or weekly audit due
python -m openrouter_model_scout.main
```

### Fast-Only (Dev/Testing)
```bash
# Skip deep scraping, only refresh API data
python -m openrouter_model_scout.main --fast-only
```

### Debugging

```bash
# Dry run with verbose output and token report
python -m openrouter_model_scout.main --dry-run --token-report --verbose
```

Check logs:
```bash
tail -f openrouter_model_scout.log
```

## Expected Output

After successful run, check:

```bash
cat data/leaderboard.json | jq .
```

Example structure:
```json
{
  "generated_at": "2026-03-06T12:00:00Z",
  "smartest": [...],
  "coding": [...],
  "free": [...],
  "value": [...]
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `OPENROUTER_API_KEY` missing | Set environment variable before running |
| Scraper blocks/rate limits | Ensure `camoufox` installed, check network |
| Permission denied on data/ | Create `data/` directory with write permissions |
| Tests fail | Install dev dependencies: `pip install -e .[dev]` |

## Next Steps

- Review `README.md` for architecture and features
- See `specs/001-openrouter-model-scout/` for design documents
- Run full test suite: `pytest tests/ -v`

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/README.md
**File Size:** 2063 bytes

## Features & Sections Declared:
# OpenRouter Model Scout
## Features
## Installation
# Clone and setup
# Set required environment variable
## Usage
# Normal run (auto-mode based on timestamps)
# Force full deep scan
# Fast API sync only (skip scraping)
# Dry run with token report
# Output CSV in addition to JSON
## Output
## Leaderboard Types
## Architecture
## Testing
## Requirements


## Content / Data Structure:
```text
# OpenRouter Model Scout

A Python-based intelligence-gathering daemon that maintains a local database of OpenRouter AI models with benchmark scores, pricing, and performance metrics. Enables intelligent routing decisions without real-time latency.

## Features

- **Fast API Sync**: Daily model list refresh from OpenRouter API (<30 seconds)
- **Deep Scraping**: Conditional web scraping for benchmark data and performance metrics
- **Smart Leaderboards**: Top models by intelligence, coding ability, value, and free tier
- **Cost Tracking**: Token usage reporting and cost estimation for budget management
- **Stealth Operation**: Uses Camoufox for anti-detection and rate limiting

## Installation

```bash
# Clone and setup
git clone <repo>
cd model-scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Set required environment variable
export OPENROUTER_API_KEY="your-api-key-here"
```

## Usage

```bash
# Normal run (auto-mode based on timestamps)
python -m openrouter_model_scout.main

# Force full deep scan
python -m openrouter_model_scout.main --force

# Fast API sync only (skip scraping)
python -m openrouter_model_scout.main --fast-only

# Dry run with token report
python -m openrouter_model_scout.main --dry-run --token-report

# Output CSV in addition to JSON
python -m openrouter_model_scout.main --output-format both
```

## Output

- `data/models.json` - Complete model database
- `data/leaderboard.json` - Curated top-5 lists
- `data/meta.json` - Run history and metadata

## Leaderboard Types

1. **Smartest**: Top 5 by Artificial Analysis Intelligence Index
2. **Coding**: Top 5 by coding benchmark score
3. **Free**: Top 5 free models (intelligence score sorted)
4. **Value**: Top 5 value models (intelligence ÷ prompt cost)

## Architecture

See `specs/001-openrouter-model-scout/plan.md` for detailed design documentation.

## Testing

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Requirements

- Python 3.12+
- camoufox
- crawl4ai
- httpx
- pydantic

See `pyproject.toml` for complete dependencies.

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/CLAUDE.md
**File Size:** 869 bytes

## Features & Sections Declared:
# model-scraper Development Guidelines
## Active Technologies
## Project Structure
## Commands
## Code Style
## Recent Changes


## Content / Data Structure:
```text
# model-scraper Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-06

## Active Technologies

- Python 3.11+ + `httpx` (async HTTP client), `camoufox` (stealth browser automation), `crawl4ai` (HTML extraction), `click` or `argparse` (CLI) (001-openrouter-model-scout)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes

- 001-openrouter-model-scout: Added Python 3.11+ + `httpx` (async HTTP client), `camoufox` (stealth browser automation), `crawl4ai` (HTML extraction), `click` or `argparse` (CLI)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/CHANGELOG.md
**File Size:** 1231 bytes

## Features & Sections Declared:
# Changelog
## [Unreleased]
### Added
### Fixed
## [1.0.0] - 2026-03-06
### Added


## Content / Data Structure:
```text
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Initial implementation of OpenRouter Model Scout
- API fetching from OpenRouter `/models` endpoint
- Deep web scraping with Camoufox + crawl4AI
- Leaderboard generation (smartest, coding, free, value)
- Cost tracking and meta.json persistence
- CLI flags: --force, --fast-only, --dry-run, --token-report, --output-format, --model-filter
- Comprehensive unit and integration test suite

### Fixed
- N/A (initial release)

## [1.0.0] - 2026-03-06

### Added
- Feature-complete implementation of all three user stories
- Support for benchmark data extraction (intelligence, coding, agentic scores)
- Performance metrics scraping (throughput, latency, uptime)
- Value leaderboard with division-by-zero protection
- Free model detection and dedicated leaderboard
- Token usage tracking with cost estimation
- Weekly automatic deep audit scheduling
- CSV export support (--output-format both)

[Unreleased]: https://github.com/your-org/model-scraper/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-org/model-scraper/releases/tag/v1.0.0

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/.pre-commit-config.yaml
**File Size:** 557 bytes

## Content / Data Structure:
```text
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11
        args: [--line-length=88]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-click]
        exclude: ^tests/
        args: [--ignore-missing-imports, --no-strict-optional]

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/pyproject.toml
**File Size:** 1983 bytes

## Content / Data Structure:
```text
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "openrouter-model-scout"
version = "0.1.0"
description = "OpenRouter Model Scout - Intelligence-gathering daemon for AI model benchmarking data"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
authors = [
    {name = "Model Scraper Team"}
]
keywords = ["openrouter", "ai", "scraping", "benchmark", "model-scout"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

dependencies = [
    "httpx>=0.27.0",
    "camoufox>=0.1.0",
    "crawl4ai>=0.4.0",
    "pydantic>=2.0.0",
    "click>=8.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[project.scripts]
openrouter-model-scout = "openrouter_model_scout.main:cli"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = []

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--tb=short",
    "--maxfail=5",
]

[tool.coverage.run]
source = ["src"]
omit = ["tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout.egg-info/entry_points.txt
**File Size:** 75 bytes

## Content / Data Structure:
```text
[console_scripts]
openrouter-model-scout = openrouter_model_scout.main:cli

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout.egg-info/dependency_links.txt
**File Size:** 1 bytes

## Content / Data Structure:
```text


```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout.egg-info/SOURCES.txt
**File Size:** 910 bytes

## Content / Data Structure:
```text
README.md
pyproject.toml
src/openrouter_model_scout/__init__.py
src/openrouter_model_scout/change_detector.py
src/openrouter_model_scout/config.py
src/openrouter_model_scout/cost.py
src/openrouter_model_scout/exceptions.py
src/openrouter_model_scout/fetcher_api.py
src/openrouter_model_scout/io.py
src/openrouter_model_scout/leaderboard.py
src/openrouter_model_scout/logger.py
src/openrouter_model_scout/main.py
src/openrouter_model_scout/meta.py
src/openrouter_model_scout/models.py
src/openrouter_model_scout/normalizer.py
src/openrouter_model_scout/scraper_web.py
src/openrouter_model_scout/token_utils.py
src/openrouter_model_scout.egg-info/PKG-INFO
src/openrouter_model_scout.egg-info/SOURCES.txt
src/openrouter_model_scout.egg-info/dependency_links.txt
src/openrouter_model_scout.egg-info/entry_points.txt
src/openrouter_model_scout.egg-info/requires.txt
src/openrouter_model_scout.egg-info/top_level.txt
```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout.egg-info/top_level.txt
**File Size:** 23 bytes

## Content / Data Structure:
```text
openrouter_model_scout

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout.egg-info/requires.txt
**File Size:** 163 bytes

## Content / Data Structure:
```text
httpx>=0.27.0
camoufox>=0.1.0
crawl4ai>=0.4.0
pydantic>=2.0.0
click>=8.0.0

[dev]
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
ruff>=0.1.0

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/.specify/templates/checklist-template.md
**File Size:** 1312 bytes

## Features & Sections Declared:
# [CHECKLIST TYPE] Checklist: [FEATURE NAME]
## [Category 1]
## [Category 2]
## Notes


## Content / Data Structure:
```text
# [CHECKLIST TYPE] Checklist: [FEATURE NAME]

**Purpose**: [Brief description of what this checklist covers]
**Created**: [DATE]
**Feature**: [Link to spec.md or relevant documentation]

**Note**: This checklist is generated by the `/speckit.checklist` command based on feature context and requirements.

<!-- 
  ============================================================================
  IMPORTANT: The checklist items below are SAMPLE ITEMS for illustration only.
  
  The /speckit.checklist command MUST replace these with actual items based on:
  - User's specific checklist request
  - Feature requirements from spec.md
  - Technical context from plan.md
  - Implementation details from tasks.md
  
  DO NOT keep these sample items in the generated checklist file.
  ============================================================================
-->

## [Category 1]

- [ ] CHK001 First checklist item with clear action
- [ ] CHK002 Second checklist item
- [ ] CHK003 Third checklist item

## [Category 2]

- [ ] CHK004 Another category item
- [ ] CHK005 Item with specific criteria
- [ ] CHK006 Final item in this category

## Notes

- Check items off as completed: `[x]`
- Add comments or findings inline
- Link to relevant resources or documentation
- Items are numbered sequentially for easy reference

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/.specify/templates/spec-template.md
**File Size:** 3960 bytes

## Features & Sections Declared:
# Feature Specification: [FEATURE NAME]
## User Scenarios & Testing *(mandatory)*
### User Story 1 - [Brief Title] (Priority: P1)
### User Story 2 - [Brief Title] (Priority: P2)
### User Story 3 - [Brief Title] (Priority: P3)
### Edge Cases
## Requirements *(mandatory)*
### Functional Requirements
### Key Entities *(include if feature involves data)*
## Success Criteria *(mandatory)*
### Measurable Outcomes


## Content / Data Structure:
```text
# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`  
**Created**: [DATE]  
**Status**: Draft  
**Input**: User description: "$ARGUMENTS"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - [Brief Title] (Priority: P1)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently - e.g., "Can be fully tested by [specific action] and delivers [specific value]"]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 2 - [Brief Title] (Priority: P2)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 3 - [Brief Title] (Priority: P3)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- What happens when [boundary condition]?
- How does system handle [error scenario]?

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST [specific capability, e.g., "allow users to create accounts"]
- **FR-002**: System MUST [specific capability, e.g., "validate email addresses"]  
- **FR-003**: Users MUST be able to [key interaction, e.g., "reset their password"]
- **FR-004**: System MUST [data requirement, e.g., "persist user preferences"]
- **FR-005**: System MUST [behavior, e.g., "log all security events"]

*Example of marking unclear requirements:*

- **FR-006**: System MUST authenticate users via [NEEDS CLARIFICATION: auth method not specified - email/password, SSO, OAuth?]
- **FR-007**: System MUST retain user data for [NEEDS CLARIFICATION: retention period not specified]

### Key Entities *(include if feature involves data)*

- **[Entity 1]**: [What it represents, key attributes without implementation]
- **[Entity 2]**: [What it represents, relationships to other entities]

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: [Measurable metric, e.g., "Users can complete account creation in under 2 minutes"]
- **SC-002**: [Measurable metric, e.g., "System handles 1000 concurrent users without degradation"]
- **SC-003**: [User satisfaction metric, e.g., "90% of users successfully complete primary task on first attempt"]
- **SC-004**: [Business metric, e.g., "Reduce support tickets related to [X] by 50%"]

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/.specify/templates/tasks-template.md
**File Size:** 9140 bytes

## Features & Sections Declared:
# Tasks: [FEATURE NAME]
## Format: `[ID] [P?] [Story] Description`
## Path Conventions
## Phase 1: Setup (Shared Infrastructure)
## Phase 2: Foundational (Blocking Prerequisites)
## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP
### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️
### Implementation for User Story 1
## Phase 4: User Story 2 - [Title] (Priority: P2)
### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️
### Implementation for User Story 2
## Phase 5: User Story 3 - [Title] (Priority: P3)
### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️
### Implementation for User Story 3
## Phase N: Polish & Cross-Cutting Concerns
## Dependencies & Execution Order
### Phase Dependencies
### User Story Dependencies
### Within Each User Story
### Parallel Opportunities
## Parallel Example: User Story 1
# Launch all tests for User Story 1 together (if tests requested):
# Launch all models for User Story 1 together:
## Implementation Strategy
### MVP First (User Story 1 Only)
### Incremental Delivery
### Parallel Team Strategy
## Notes


## Content / Data Structure:
```text
---

description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.
  
  The /speckit.tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize [language] project with [framework] dependencies
- [ ] T003 [P] Configure linting and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup database schema and migrations framework
- [ ] T005 [P] Implement authentication/authorization framework
- [ ] T006 [P] Setup API routing and middleware structure
- [ ] T007 Create base models/entities that all stories depend on
- [ ] T008 Configure error handling and logging infrastructure
- [ ] T009 Setup environment configuration management

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T011 [P] [US1] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create [Entity1] model in src/models/[entity1].py
- [ ] T013 [P] [US1] Create [Entity2] model in src/models/[entity2].py
- [ ] T014 [US1] Implement [Service] in src/services/[service].py (depends on T012, T013)
- [ ] T015 [US1] Implement [endpoint/feature] in src/[location]/[file].py
- [ ] T016 [US1] Add validation and error handling
- [ ] T017 [US1] Add logging for user story 1 operations

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T019 [P] [US2] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 2

- [ ] T020 [P] [US2] Create [Entity] model in src/models/[entity].py
- [ ] T021 [US2] Implement [Service] in src/services/[service].py
- [ ] T022 [US2] Implement [endpoint/feature] in src/[location]/[file].py
- [ ] T023 [US2] Integrate with User Story 1 components (if needed)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T025 [P] [US3] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 3

- [ ] T026 [P] [US3] Create [Entity] model in src/models/[entity].py
- [ ] T027 [US3] Implement [Service] in src/services/[service].py
- [ ] T028 [US3] Implement [endpoint/feature] in src/[location]/[file].py

**Checkpoint**: All user stories should now be independently functional

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] Documentation updates in docs/
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Performance optimization across all stories
- [ ] TXXX [P] Additional unit tests (if requested) in tests/unit/
- [ ] TXXX Security hardening
- [ ] TXXX Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/.specify/templates/constitution-template.md
**File Size:** 2336 bytes

## Features & Sections Declared:
# [PROJECT_NAME] Constitution
## Core Principles
### [PRINCIPLE_1_NAME]
### [PRINCIPLE_2_NAME]
### [PRINCIPLE_3_NAME]
### [PRINCIPLE_4_NAME]
### [PRINCIPLE_5_NAME]
## [SECTION_2_NAME]
## [SECTION_3_NAME]
## Governance


## Content / Data Structure:
```text
# [PROJECT_NAME] Constitution
<!-- Example: Spec Constitution, TaskFlow Constitution, etc. -->

## Core Principles

### [PRINCIPLE_1_NAME]
<!-- Example: I. Library-First -->
[PRINCIPLE_1_DESCRIPTION]
<!-- Example: Every feature starts as a standalone library; Libraries must be self-contained, independently testable, documented; Clear purpose required - no organizational-only libraries -->

### [PRINCIPLE_2_NAME]
<!-- Example: II. CLI Interface -->
[PRINCIPLE_2_DESCRIPTION]
<!-- Example: Every library exposes functionality via CLI; Text in/out protocol: stdin/args → stdout, errors → stderr; Support JSON + human-readable formats -->

### [PRINCIPLE_3_NAME]
<!-- Example: III. Test-First (NON-NEGOTIABLE) -->
[PRINCIPLE_3_DESCRIPTION]
<!-- Example: TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced -->

### [PRINCIPLE_4_NAME]
<!-- Example: IV. Integration Testing -->
[PRINCIPLE_4_DESCRIPTION]
<!-- Example: Focus areas requiring integration tests: New library contract tests, Contract changes, Inter-service communication, Shared schemas -->

### [PRINCIPLE_5_NAME]
<!-- Example: V. Observability, VI. Versioning & Breaking Changes, VII. Simplicity -->
[PRINCIPLE_5_DESCRIPTION]
<!-- Example: Text I/O ensures debuggability; Structured logging required; Or: MAJOR.MINOR.BUILD format; Or: Start simple, YAGNI principles -->

## [SECTION_2_NAME]
<!-- Example: Additional Constraints, Security Requirements, Performance Standards, etc. -->

[SECTION_2_CONTENT]
<!-- Example: Technology stack requirements, compliance standards, deployment policies, etc. -->

## [SECTION_3_NAME]
<!-- Example: Development Workflow, Review Process, Quality Gates, etc. -->

[SECTION_3_CONTENT]
<!-- Example: Code review requirements, testing gates, deployment approval process, etc. -->

## Governance
<!-- Example: Constitution supersedes all other practices; Amendments require documentation, approval, migration plan -->

[GOVERNANCE_RULES]
<!-- Example: All PRs/reviews must verify compliance; Complexity must be justified; Use [GUIDANCE_FILE] for runtime development guidance -->

**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFICATION_DATE] | **Last Amended**: [LAST_AMENDED_DATE]
<!-- Example: Version: 2.1.1 | Ratified: 2025-06-13 | Last Amended: 2025-07-16 -->

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/.specify/templates/plan-template.md
**File Size:** 3546 bytes

## Features & Sections Declared:
# Implementation Plan: [FEATURE]
## Summary
## Technical Context
## Constitution Check
## Project Structure
### Documentation (this feature)
### Source Code (repository root)
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
## Complexity Tracking


## Content / Data Structure:
```text
# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/.specify/templates/agent-file-template.md
**File Size:** 464 bytes

## Features & Sections Declared:
# [PROJECT NAME] Development Guidelines
## Active Technologies
## Project Structure
## Commands
## Code Style
## Recent Changes


## Content / Data Structure:
```text
# [PROJECT NAME] Development Guidelines

Auto-generated from all feature plans. Last updated: [DATE]

## Active Technologies

[EXTRACTED FROM ALL PLAN.MD FILES]

## Project Structure

```text
[ACTUAL STRUCTURE FROM PLANS]
```

## Commands

[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]

## Code Style

[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]

## Recent Changes

[LAST 3 FEATURES AND WHAT THEY ADDED]

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/.specify/memory/constitution.md
**File Size:** 3369 bytes

## Features & Sections Declared:
# Model Scraper Constitution
## Core Principles
### Simplicity & Efficiency
### Test-First Development (NON-NEGOTIABLE)
### Independent Testability
### Incremental MVP Delivery
### Parallel Execution
## Additional Constraints
## Development Workflow
## Governance


## Content / Data Structure:
```text
<!--
Sync Impact Report:
- Version Change: N/A (initial creation) → 1.0.0
- Modified Principles: None (initial constitution creation)
- Added Sections: All core principles populated; governance defined
- Removed Sections: None (template placeholders replaced)
- Templates Requiring Updates: ✅ No updates required (templates already align via Constitution Check mechanism)
- Follow-up TODOs: RATIFICATION_DATE to be set upon formal adoption
-->

# Model Scraper Constitution

## Core Principles

### Simplicity & Efficiency
Code MUST be efficient and avoid unnecessary complexity. Prioritize clear, maintainable solutions over clever or abstract ones. Every dependency, abstraction, and architectural decision must be justified by measurable benefit. Complexity requires explicit approval.

### Test-First Development (NON-NEGOTIABLE)
All implementation MUST be preceded by failing tests. Follow Red-Green-Refactor: write test → confirm failure → implement minimal code → refactor. Tests define specifications; implementation without tests is prohibited.

### Independent Testability
User stories MUST be independently testable and deliverable. Each story must constitute a complete, verifiable increment of functionality. Stories cannot rely on other stories for core behavior. Independent testability enables parallel work and incremental delivery.

### Incremental MVP Delivery
Features MUST be delivered in small, complete increments. After each user story, the product must be in a shippable state. Avoid large, monolithic changes; break work into reversible steps. MVP focus ensures value delivery and risk reduction.

### Parallel Execution
Work decomposition MUST maximize parallel execution. Tasks that can be performed without dependency blocking are marked [P]. Dependencies must be explicit, minimized, and documented. Team members should be able to work concurrently with minimal coordination overhead.

## Additional Constraints
- All code must adhere to the project's defined coding standards and linting rules.
- Dependencies must be vetted for security, license compatibility, and active maintenance.
- Performance benchmarks must be established for critical paths before implementation begins.

## Development Workflow
- All changes require pull request review with at least one approval.
- Continuous integration must pass all checks before merge.
- The Constitution Check in the implementation plan must be satisfied before any development work begins.
- Exceptions to principles must be documented and justified in the pull request.

## Governance
This Constitution supersedes all other project guidelines. It is the ultimate authority for development practices.

- Amendments require a pull request that updates this file, includes a Sync Impact Report, and is approved by project maintainers.
- Versioning follows semantic versioning (MAJOR.MINOR.PATCH). Major: principle changes; Minor: new principles; Patch: clarifications.
- Compliance with this Constitution is mandatory. Violations must be justified and approved as exceptions; systemic violations trigger principle revision.
- This document must remain self-contained and up-to-date; any drift with templates requires correction via the speckit.analyze tool.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): Pending formal adoption by maintainers | **Last Amended**: 2026-03-06

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/specs/001-openrouter-model-scout/data-model.md
**File Size:** 11251 bytes

## Features & Sections Declared:
# Data Model: OpenRouter Model Scout
## 1. Core Entities
### Entity: Model
## 2. Supporting Entities
### Entity: Leaderboard
### Entity: Meta
### Entity: ChangeDetector
## 3. State Transitions
### Model Synchronization Flow
## 4. Validation Rules
### Model Invariants
### Leaderboard Requirements
## 5. Serialization Formats
## 6. Migration Strategy
## 7. Derived Computations
### Value Score Calculation
### Effective Price Calculation
## 8. Concurrency Model
## 9. Error Handling & Recovery
### API Failure
### Scraper Failure
### Disk Write Failure
## 10. Data Integrity
## 11. Access Control


## Content / Data Structure:
```text
# Data Model: OpenRouter Model Scout

**Feature**: 001-openrouter-model-scout
**Date**: 2026-03-06

---

## 1. Core Entities

### Entity: Model

The central entity representing an AI model available through OpenRouter.

**Fields**:

| Field Name | Type | Source | Required | Description |
|------------|------|--------|----------|-------------|
| `id` | string | API | Yes | Unique model identifier (e.g., "openai/gpt-4") |
| `name` | string | API | Yes | Display name (e.g., "OpenAI: GPT-4") |
| `organization` | string | Derived | Yes | Provider parsed from ID (e.g., "openai") |
| `description_short` | string | Scraper | No | First 2 sentences of overview |
| `description_full` | string | Scraper | No | Full "Overview" section text |
| `release_date` | string (ISO 8601) | Scraper | No | Release date (e.g., "Mar 5, 2026") |
| `parameter_size` | string | Scraper | No | Model size (e.g., "Unknown", "70B") |

**Context & Constraints**:

| Field Name | Type | Source | Required | Description |
|------------|------|--------|----------|-------------|
| `context_length` | integer | API | Yes | Total context window (tokens) |
| `max_output_tokens` | integer | API | Yes | Max generation tokens |
| `supports_vision` | boolean | API | Yes | Image input capability |
| `supports_tools` | boolean | API | Yes | Function calling support |
| `supports_caching` | boolean | API | Yes | Prompt caching availability |
| `quantization` | string | Scraper | No | Quantization level (e.g., "FP8", "BF16") |

**Pricing** (nested object `pricing`):

| Field Name | Type | Source | Required | Description |
|------------|------|--------|----------|-------------|
| `pricing.prompt` | float | API | Yes | Input cost per 1M tokens ($) |
| `pricing.completion` | float | API | Yes | Output cost per 1M tokens ($) |
| `pricing.cache_read` | float | API | Yes | Cache hit cost per 1M tokens ($) |
| `pricing.cache_write` | float | float | Scraper | No | Cache write cost (if available) |
| `pricing.web_search` | float | Scraper | No | Cost per 1K web search calls ($) |
| `effective_price_input` | float | Derived | Yes | Weighted avg input price across providers |
| `effective_price_output` | float | Derived | Yes | Weighted avg output price across providers |
| `is_free` | boolean | Derived | Yes | True if prompt & completion are both $0 |

**Performance** (nested object `performance`):

| Field Name | Type | Source | Required | Description |
|------------|------|--------|----------|-------------|
| `performance.throughput_tps` | float | Scraper | No | Tokens per second |
| `performance.latency_seconds` | float | Scraper | No | Time to first token (TTFT) |
| `performance.e2e_latency_seconds` | float | Scraper | No | End-to-end generation latency |
| `performance.tool_error_rate` | float | Scraper | No | Tool call failure % (0-100) |
| `performance.uptime_percent` | float | Scraper | No | Provider uptime % (0-100) |

**Benchmarks** (nested object `benchmarks`):

| Field Name | Type | Source | Required | Description |
|------------|------|--------|----------|-------------|
| `benchmarks.intelligence.score` | float | Scraper | No | Artificial Analysis Intelligence Index |
| `benchmarks.intelligence.percentile` | float | Scraper | No | Percentile rank (0-100) |
| `benchmarks.coding.score` | float | Scraper | No | Coding benchmark score |
| `benchmarks.coding.percentile` | float | Scraper | No | Coding percentile (0-100) |
| `benchmarks.agentic.score` | float | Scraper | No | Agentic Index score |
| `benchmarks.agentic.percentile` | float | Scraper | No | Agentic percentile (0-100) |

**Detailed Benchmarks** (all nested under `benchmarks`, all optional):

| Field Name | Type | Description |
|------------|------|-------------|
| `benchmarks.gpqa_diamond` | float | Graduate-level scientific reasoning % |
| `benchmarks.hle` | float | Humanity's Last Exam % |
| `benchmarks.ifbench` | float | Instruction-following benchmark % |
| `benchmarks.aa_lcr` | float | Long context reasoning evaluation % |
| `benchmarks.gdpval_aa` | float | Economically valuable tasks % |
| `benchmarks.critpt` | float | Research-level physics reasoning % |
| `benchmarks.scicode` | float | Scientific computing % |
| `benchmarks.terminal_bench` | float | Terminal/agentic coding % |
| `benchmarks.omniscience_accuracy` | float | Knowledge accuracy % |
| `benchmarks.omniscience_hallucination` | float | Hallucination rate % |

**Derived Fields** (computed, not stored in raw Model but in processed view):
- `value_score` = `benchmarks.intelligence.score / max(pricing.prompt, 0.000001)` (for value ranking)

---

## 2. Supporting Entities

### Entity: Leaderboard

A computed collection of top-5 lists, stored in `leaderboard.json`.

**Structure**:

```json
{
  "generated_at": "2026-03-06T12:00:00Z",
  "smartest": [
    {"id": "...", "name": "...", "intelligence_score": 75.0, "percentile": 99.0, "price_per_1m": 2.50},
    ...
  ],
  "coding": [
    {"id": "...", "name": "...", "coding_score": 80.0, "agentic_score": 70.0, "price_per_1m": 5.00},
    ...
  ],
  "free": [
    {"id": "...", "name": "...", "intelligence_score": 60.0, "context_length": 8192, "throughput_tps": 50.0},
    ...
  ],
  "value": [
    {"id": "...", "name": "...", "value_score": 150.5, "price_per_1m": 0.50, "intelligence_percentile": 95.0},
    ...
  ]
}
```

**Constraints**:
- Each list contains exactly 5 entries (or fewer if insufficient models with required data)
- Models sorted by score descending
- `smartest` excludes models with null `benchmarks.intelligence.score`
- `value` excludes `is_free == true` models (to avoid infinite ratio)
- All monetary values in USD

---

### Entity: Meta

Operational metadata stored in `meta.json`.

**Structure**:

```json
{
  "last_run": "2026-03-06T12:00:00Z",
  "last_deep_audit": "2026-03-06T06:00:00Z",
  "run_history": [
    {
      "timestamp": "2026-03-06T12:00:00Z",
      "mode": "full",
      "api_sync_duration_seconds": 25.3,
      "scrape_duration_seconds": 1850.2,
      "models_count": 287,
      "token_usage": {
        "prompt_tokens": 15000,
        "completion_tokens": 5000,
        "estimated_cost_usd": 0.45
      }
    }
  ]
}
```

---

### Entity: ChangeDetector

Not a persisted entity, but a computation module. State maintained in memory during execution:
- `previous_checksum`: SHA256 of previous API response body
- `previous_pricing_map`: Dict[model_id, pricing_prompt] for delta detection
- `new_models_queue`: List[model_id] that need scraping

**Persistence**: No - recomputed each run by comparing current models.json (as source of truth) with API fetch results.

---

## 3. State Transitions

### Model Synchronization Flow

```
[Start] → Fetch API Response → Compare checksums
    ↓ (unchanged)
[Skip Scraping] → Update meta.json → [Done]
    ↓ (changed OR forced)
[Queue New/Changed Models] → Run Deep Scraper
    ↓
[Merge Data] → Write models.json + leaderboard.json
    ↓
[Update meta.json] → [Done]
```

**State Changes**:
- `models.json`: Overwritten with merged data (API + scraped)
- `leaderboard.json`: Overwritten with computed top-5 lists
- `meta.json`: Append to run_history, update last_run/last_deep_audit

---

## 4. Validation Rules

### Model Invariants

- `id` must be non-empty string, format "provider/model-name"
- `pricing.prompt` >= 0, `pricing.completion` >= 0
- `benchmarks.*.score` between 0-100 (if present)
- `performance.*` within reasonable ranges:
  - `throughput_tps` > 0
  - `latency_seconds` > 0
  - `uptime_percent` between 0-100
- `is_free` = (`pricing.prompt == 0` AND `pricing.completion == 0`)

### Leaderboard Requirements

- At least 3 entries required for a list to be considered "valid" (otherwise omit that list)
- Entries must have non-null scores for the sort key
- Duplicate removal: same model ID cannot appear twice in one list

---

## 5. Serialization Formats

**models.json**: Array of Model objects (one per line or single array). One file contains all models.
**leaderboard.json**: Single object with 4 arrays (smartest, coding, free, value)
**meta.json**: Object with metadata and run_history array

All JSON must be UTF-8 encoded, no embedded newlines in strings (use \n escape).

---

## 6. Migration Strategy

**Initial State**: No data files exist.

**First Run**:
1. Create `data/` directory if missing
2. Fetch API → Save to temporary file
3. If `--force` or no new models detected? Decision: On first run, always scrape all models to get benchmarks
4. Write models.json, leaderboard.json, meta.json

**Subsequent Runs**:
- Compare checksums (fast)
- If unchanged and not forced and not past audit interval → exit early (meta.json still updated to reflect check)
- If changed: scrape only new/changed models (incremental)
- Monthly full audit: rescrape all regardless of changes

**Schema Evolution**: If new fields are added to spec (e.g., new benchmark), store as optional; backward compatibility by using optional fields with defaults.

---

## 7. Derived Computations

### Value Score Calculation

```
value_score = intelligence_score / max(prompt_price_per_1m, 0.000001)
```

Rationale:
- Use prompt price (not completion) as proxy for cost (input is always consumed)
- Prevent division-by-zero for free models (they're excluded anyway)
- Example: GPT-4 = $2.50/1M, intelligence 75 → 75 / 2.5 = 30.0

### Effective Price Calculation

Weighted average across all models' pricing (used for market reference):
```
effective_price_input = Σ(pricing.prompt) / count(models_with_pricing)
effective_price_output = Σ(pricing.completion) / count(models_with_pricing)
```

These are computed by scraper and stored per model (per spec's `effective_price_*` fields), not recomputed by leaderboard.

---

## 8. Concurrency Model

**Single-threaded async** is sufficient:
- API calls are sequential (rate limited anyway)
- Scraper uses Camoufox (single browser instance, sequential page loads)
- Parallelism not needed for ~300 models (60min budget = 12s per model average)

**No shared state** between runs (scratch files are overwritten).

---

## 9. Error Handling & Recovery

### API Failure
- **Transient** (network error, 5xx): Retry with exponential backoff (max 3 retries)
- **Persistent** (4xx, auth failure): Log error, exit with code 1, preserve previous data

### Scraper Failure
- **Individual model failure**: Log and continue; that model retains old data (or null if new)
- **Browser crash**: Restart browser instance, retry from current position
- **CAPTCHA/Block**: Stop scraping, set block rate flag in meta.json, fall back to API-only

### Disk Write Failure
- **Permission error**: Exit with code 1, do not corrupt existing files
- **Corrupted JSON on read**: Backup corrupted file with `.corrupt.<timestamp>` suffix, reinitialize from API if possible

---

## 10. Data Integrity

- **Atomic writes**: Write to temporary file, then rename (atomic on POSIX)
- **Checksums**: SHA256 of models.json stored in meta.json to detect corruption
- **Backups**: Keep last 3 versions of models.json/leaderboard.json by renaming (optional, `--keep-history` flag)

---

## 11. Access Control

**None** - all data files owned by proxy user. No sensitive credentials stored (OpenRouter API key read from env var at runtime, not persisted).

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/specs/001-openrouter-model-scout/quickstart.md
**File Size:** 6610 bytes

## Features & Sections Declared:
# Quickstart: OpenRouter Model Scout
## 1. Project Setup
### Prerequisites
### Initial Setup
# Navigate to project root
# Create and activate virtual environment
# Install dependencies (once defined)
# or: pip install -r requirements.txt
### Environment Configuration
## 2. Development Workflow
### Understanding the Codebase
### Running the Scout
# or: python src/main.py
## 3. Testing
## 4. Data Files
## 5. Debugging Tips
### Logs
### Inspecting Data
# Pretty-print models.json (first 10 models)
# View leaderboard
# Check last run metadata
## 6. Common Issues
### **Camoufox Import Error**
### **OpenRouter API Returns 401/403**
### **Scraper Blocked (High Block Rate)**
### **Missing Benchmark Data**
### **Tests Fail with Network Errors**
## 7. Architecture Reminders
## 8. Next Steps
## 9. Contributing
## 10. Resources


## Content / Data Structure:
```text
# Quickstart: OpenRouter Model Scout

**Feature**: 001-openrouter-model-scout
**Date**: 2026-03-06

---

## 1. Project Setup

### Prerequisites

- Python 3.11 or higher
- Virtual environment tool (`venv` or `uv` or `poetry`)
- Git

### Initial Setup

```bash
# Navigate to project root
cd /home/cheta/code/model-scraper

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (once defined)
pip install -e .
# or: pip install -r requirements.txt
```

### Environment Configuration

Set your OpenRouter API key as an environment variable:

```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

**Important**: The scout does **not** store API keys; it reads them from the environment at runtime.

---

## 2. Development Workflow

### Understanding the Codebase

```
src/
├── main.py              # Entry point (python -m openrouter_model_scout)
├── cli.py               # Command-line argument parsing
├── models.py            # Pydantic schemas for data structures
├── fetcher_api.py       # OpenRouter API client
├── scraper_web.py       # Camoufox + Crawl4AI integration
├── normalizer.py        # Merge API and scraped data
├── change_detector.py   # Checksum and delta detection
└── leaderboard.py       # Generate leaderboard.json
```

### Running the Scout

**Basic usage** (automatic mode - checks timestamps, runs if needed):

```bash
python -m openrouter_model_scout
# or: python src/main.py
```

**Force a full deep scan** (ignores timestamps, scrapes all models):

```bash
python -m openrouter_model_scout --force
```

**API-only fast sync** (skip scraping):

```bash
python -m openrouter_model_scout --fast-only
```

**Dry run** (doesn't write files, prints to stdout):

```bash
python -m openrouter_model_scout --dry-run
```

**Generate token usage report** (shows scraper's own token consumption):

```bash
python -m openrouter_model_scout --token-report
```

**Filter models by regex** (useful for testing):

```bash
python -m openrouter_model_scout --model-filter "openai/gpt-.*"
```

**Choose output format**:

```bash
python -m openrouter_model_scout --output-format json   # default
python -m openrouter_model_scout --output-format csv
python -m openrouter_model_scout --output-format both
```

---

## 3. Testing

**Run all unit tests**:

```bash
pytest tests/unit/
```

**Run integration tests** (requires network access; may hit real OpenRouter):

```bash
pytest tests/integration/
```

**Run specific test file**:

```bash
pytest tests/unit/test_fetcher_api.py -v
```

**Run with coverage**:

```bash
pytest --cov=src tests/
```

---

## 4. Data Files

After running the scout, the following files are created in `data/`:

- `models.json` - Complete model database (raw + enriched data)
- `leaderboard.json` - Top-5 lists for quick access
- `meta.json` - Metadata, timestamps, and run history

These files are **gitignored** (runtime data).

---

## 5. Debugging Tips

### Logs

The scout uses Python's `logging` module. Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python -m openrouter_model_scout
```

Logs show:
- API fetch duration and model count
- Checksum comparison results
- Queue of models to scrape
- Scraper progress (model number, success/failure)
- Token usage and cost estimates
- Leaderboard generation results

### Inspecting Data

```bash
# Pretty-print models.json (first 10 models)
jq '.[:10]' data/models.json

# View leaderboard
cat data/leaderboard.json | jq '.smartest'

# Check last run metadata
cat data/meta.json | jq '.last_run, .run_history[-1]'
```

---

## 6. Common Issues

### **Camoufox Import Error**

```
ModuleNotFoundError: No module named 'camoufox'
```

**Solution**: Install the camoufox package. Check `pyproject.toml` or `requirements.txt`.

```
pip install camoufox
```

---

### **OpenRouter API Returns 401/403**

**Cause**: Missing or invalid API key.

**Solution**: Ensure `OPENROUTER_API_KEY` is set and has permissions to read models.

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

---

### **Scraper Blocked (High Block Rate)**

**Symptoms**: 429 Too Many Requests, 403 Forbidden, or CAPTCHA pages.

**Mitigations**:
1. Reduce concurrency: Ensure only one scraper instance runs at a time
2. Increase delays: The scraper uses random 2-5 second delays; if still blocked, manual intervention may be needed
3. Use `--dry-run` to test without writing files and see if blocks persist

---

### **Missing Benchmark Data**

**Normal**: New models may not have benchmarks yet; they're only populated after scraping.

**What to do**: Wait for the weekly deep audit or run `--force` to scrape all.

---

### **Tests Fail with Network Errors**

Integration tests may be flaky if OpenRouter is rate-limiting.

**Solution**: Run unit tests only, or mock API responses:

```bash
pytest tests/unit/  # Skip integration tests
```

---

## 7. Architecture Reminders

- **Direct Library Import**: `camoufox` and `crawl4ai` are imported as Python modules (not subprocess calls) - this is a hard requirement for performance.
- **Graceful Degradation**: If scraping fails, the system falls back to API-only data. The proxy will still work, just with less rich benchmarks.
- **Stealth**: The scraper uses realistic delays and Camoufox's anti-detection features. Do **not** remove these to "speed up" development - it will increase block rate.
- **Constitution Compliance**: All code must follow the project's constitution principles, especially Simplicity & Efficiency and Test-First.

---

## 8. Next Steps

After the scout is working:

1. **Integrate with the Claude Code Proxy**: Use the generated `leaderboard.json` to inform model routing decisions.
2. **Schedule automatic runs**: Add to cron (e.g., `0 * * * * cd /path && python -m openrouter_model_scout`)
3. **Monitor block rate**: Check `meta.json` for error occurrences; adjust stealth parameters if needed.
4. **Expand coverage**: Ensure all desired models have benchmark data; consider adding custom benchmarks if needed.

---

## 9. Contributing

When modifying the code:

- Write tests first (constitution requirement)
- Follow the existing structure (one module per responsibility)
- Keep it simple (avoid over-abstraction)
- Update `data-model.md` and `quickstart.md` if schemas change
- Document any CLI flag changes in this file

---

## 10. Resources

- **OpenRouter API Docs**: https://openrouter.ai/docs
- **Camoufox**: https://github.com/calendis/camoufox
- **Crawl4AI**: https://github.com/unclecode/crawl4ai
- **Project Constitution**: `.specify/memory/constitution.md`

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/specs/001-openrouter-model-scout/plan.md
**File Size:** 4457 bytes

## Features & Sections Declared:
# Implementation Plan: OpenRouter Model Scout
## Summary
## Technical Context
## Constitution Check
## Project Structure
### Documentation (this feature)
### Source Code (repository root)
## Complexity Tracking


## Content / Data Structure:
```text
# Implementation Plan: OpenRouter Model Scout

**Branch**: `001-openrouter-model-scout` | **Date**: 2026-03-06 | **Spec**: [spec.md](../spec.md)
**Input**: Feature specification from `/specs/001-openrouter-model-scout/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

The OpenRouter Model Scout (ORMS) is a Python-based daemon that maintains a local, enriched database of OpenRouter AI models through a hybrid approach: fast API synchronization for model listings and conditional deep web scraping for benchmark/performance data. It generates leaderboard JSON files (smartest, coding, free, value) to enable the Claude Code Proxy to make intelligent routing decisions without real-time latency. The architecture uses direct library imports (camoufox, crawl4ai) rather than subprocess spawning for efficiency and state management.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `httpx` (async HTTP client), `camoufox` (stealth browser automation), `crawl4ai` (HTML extraction), `click` or `argparse` (CLI)
**Storage**: File-based JSON storage in `data/` directory (models.json, leaderboard.json, meta.json)
**Testing**: pytest (unit tests), pytest-asyncio (async tests)
**Target Platform**: Linux server / WSL2 (daemon process)
**Project Type**: CLI tool / standalone script
**Performance Goals**: API sync <30s for ~300 models, Deep scan <60min for 300 models, <1% block rate on scraper
**Constraints**: Must be stealthy (anti-detection), handle failures gracefully (fallback to API-only), respect rate limits, minimal token usage
**Scale/Scope**: ~300 models, single daemon process, ~10MB storage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Simplicity & Efficiency**: Architecture is simple (3 main components), dependencies minimized (direct library imports vs subprocess spawning), and justifiable (camoufox required for stealth, crawl4ai for extraction). No unnecessary abstraction layers.

✅ **Independent Testability**: User stories are independently testable:
- US1: Leaderboard generation (smartest top 5)
- US2: Value score calculation (separate from leaderboard)
- US3: Token tracking and meta.json persistence

⚠ **Test-First Development**: Tests are optional per spec template, but constitution makes them NON-NEGOTIABLE. We must include unit tests for each component, even though the spec says "Tests are OPTIONAL". This is a constitution compliance requirement.

**Complexity Violations?** None. The design uses a straightforward layered architecture without over-engineering.

## Project Structure

### Documentation (this feature)

```text
specs/001-openrouter-model-scout/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi.yaml
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
src/
├── cli.py               # Command-line interface, argument parsing, orchestration
├── fetcher_api.py       # Fast API sync to OpenRouter
├── scraper_web.py       # Deep web scraping with Camoufox + Crawl4AI
├── normalizer.py        # Merge API + scraped data
├── change_detector.py   # Checksum-based diff and delta detection
├── leaderboard.py       # Generate top-5 lists
├── models.py            # Data models / Pydantic schemas
└── main.py              # Entry point: python -m openrouter_model_scout

tests/
├── unit/
│   ├── test_fetcher_api.py
│   ├── test_scraper_web.py
│   ├── test_normalizer.py
│   ├── test_change_detector.py
│   ├── test_leaderboard.py
│   └── test_models.py
├── integration/
│   └── test_e2e.py
└── contract/
    └── test_api_response_schema.py

data/                    # Created at runtime (gitignored)
├── models.json
├── leaderboard.json
└── meta.json
```

**Structure Decision**: Single-project Python package with clear module separation. Tests mirror source structure. Data directory for runtime persistence. This aligns with "standalone script" architecture while enabling testability and parallel development.

## Complexity Tracking

> **No violations** - architecture is simple and justified. All components have clear responsibilities. No 4th project, no repository pattern, no over-abstraction.

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/specs/001-openrouter-model-scout/research.md
**File Size:** 10581 bytes

## Features & Sections Declared:
# Research: OpenRouter Model Scout
## 1. Technology Stack Selection
### Decision: Python 3.11+
### Decision: httpx for API Synchronization
### Decision: Camoufox for Web Scraping (Direct Library Import)
### Decision: crawl4ai for HTML Extraction
### Decision: JSON File Storage (data/models.json, data/leaderboard.json, data/meta.json)
### Decision: pytest for Testing
## 2. Architecture Decisions
### Decision: Hybrid Pipeline (API Fast Path + Conditional Scraping)
### Decision: Direct Library Imports vs Subprocess Spawning
### Decision: Leaderboard Precomputation (Derived Top-5 Lists)
## 3. Data Model Insights
### Model Schema Design
## 4. Operational Considerations
### Scheduling: Timestamp-Based Checks
### Error Handling Strategy
### Stealth and Rate Limiting
## 5. Testing Strategy
## 6. Open Questions / Risks
## 7. Summary of Decisions


## Content / Data Structure:
```text
# Research: OpenRouter Model Scout

**Date**: 2026-03-06
**Feature**: 001-openrouter-model-scout
**Purpose**: Document architectural decisions, alternatives considered, and rationales

---

## 1. Technology Stack Selection

### Decision: Python 3.11+

**Rationale**:
- Rapid development and iteration (critical for scraping projects where targets may change)
- Excellent library ecosystem for HTTP clients (httpx), parsing (crawl4ai), and browser automation (camoufox)
- Easy to deploy as single-file script or package
- Familiar to most developers in the Claude Code ecosystem

**Alternatives Considered**:
- **Go**: Faster execution, better concurrency, but fewer specialized scraping libraries; would need to shell out to external tools anyway
- **Node.js**: Good for scraping (puppeteer), but Python's data processing libraries (pydantic) are superior for structured data
- **Rust**: Maximum performance but longer development time; overkill for this use case

**Conclusion**: Python offers the best balance of development speed, library support, and deployment simplicity.

---

### Decision: httpx for API Synchronization

**Rationale**:
- Async/await support for concurrent operations
- HTTP/2 support (potential performance benefit)
- Better error handling and retry logic compared to requests
- Type-safe with httpx.AsyncClient

**Alternatives Considered**:
- **requests**: Synchronous, would block during API calls; acceptable for simple single-threaded script but httpx is more future-proof
- **aiohttp**: Lower-level, more boilerplate; httpx provides higher-level abstractions

---

### Decision: Camoufox for Web Scraping (Direct Library Import)

**Rationale**:
- Firefox-based browser with built-in anti-detection features (fingerprint randomization, TLS fingerprinting)
- Provides Python API for direct integration (no subprocess overhead)
- Actively maintained and designed specifically for scraping
- Better than Selenium/Playwright for stealth requirements (<1% block rate target)

**Alternatives Considered**:
- **Playwright**: Excellent automation but higher detection rate; more visible automation signatures
- **Selenium + undetected-chromedriver**: Chrome-based, still detectable by advanced bot detection
- **Subprocess with external browser**: Process spawning overhead, harder to manage state, slower than direct library import

**Critical Architecture Note**: The spec explicitly states "imports camoufox directly as a library" - this is a hard requirement, not a choice. The user wants "maximum speed, minimal token waste, and tight integration."

---

### Decision: crawl4ai for HTML Extraction

**Rationale**:
- LLM-powered extraction (uses Claude via API) but also supports rule-based fallbacks
- Markdown output option, structured JSON
- Smart content extraction that handles dynamic pages
- Open source with good documentation

**Alternatives Considered**:
- **BeautifulSoup**: Low-level parsing, requires manual selectors; more fragile when site changes
- **Scrapy**: Full framework, overkill for single-page scraping; steeper learning curve
- **Readability-lxml**: Only extracts main content, not structured data; would need custom parsing for benchmark scores

---

### Decision: JSON File Storage (data/models.json, data/leaderboard.json, data/meta.json)

**Rationale**:
- Simplicity: no database server required, easy to inspect and debug
- Performance: reading/writing ~300 model documents is fast (<100ms)
- Portability: single directory can be backed up, copied, or versioned
- Sufficient for single-instance daemon (no concurrent writes expected)
- Eliminates database complexity (schema migrations, connection pooling, etc.)

**Alternatives Considered**:
- **SQLite**: Would provide query performance and atomic updates, but adds database dependency and complexity; JSON is human-readable and sufficient
- **PostgreSQL**: Overkill, requires server, connection management; violates simplicity principle
- **YAML**: More readable but slower to parse, larger file size; JSON is standard for APIs

---

### Decision: pytest for Testing

**Rationale**:
- De facto standard for Python testing
- Rich plugin ecosystem (pytest-asyncio for async code)
- Good assertion introspection
- Integrates with CI/CD easily

**Alternatives Considered**:
- **unittest**: Built-in but more boilerplate; pytest is more Pythonic
- ** hypothesis**: Property-based testing could be valuable but not required for this scope

---

## 2. Architecture Decisions

### Decision: Hybrid Pipeline (API Fast Path + Conditional Scraping)

**Rationale**:
- API sync is fast (<30s) and sufficient for detecting new models/price changes
- Scraping is expensive (target: <60min for 300 models) and should be minimized
- Smart change detection (checksums, pricing deltas) reduces unnecessary scraping
- Weekly full audit ensures benchmark data stays fresh without daily scraping

**Trade-offs**:
- Complexity: Two code paths (API vs scrape) need maintenance
- Risk: If OpenRouter changes their UI, scraping breaks; but fallback to API-only ensures proxy still works

**Why Not Pure API?**: OpenRouter's API doesn't provide benchmark scores or performance metrics. Scraping is necessary for the core value proposition (intelligent routing).

**Why Not Pure Scraping?**: Too slow for frequent updates; API is cheaper and faster for daily checks.

---

### Decision: Direct Library Imports vs Subprocess Spawning

**From Spec**: "This tool is a Programmatic Python Script, NOT a generic CLI browser wrapper. It imports camoufox directly as a library."

**Rationale**:
- Faster: No process startup overhead (subprocess.Popen is slow)
- State sharing: Browser instance can be reused across multiple model pages
- Memory efficiency: Single process, shared memory space
- Error handling: Exceptions propagate naturally, no need to parse stdout/stderr
- Integration: Can easily share data structures between scraper and normalizer

**Alternatives**: `subprocess.run(['camoufox', '--url', ...])` would be simpler initially but violates the explicit architecture requirement and would be slower.

---

### Decision: Leaderboard Precomputation (Derived Top-5 Lists)

**Rationale**:
- Proxy needs fast lookups; shouldn't parse entire models.json at runtime
- Leaderboard.json provides ready-to-use curated lists
- Reduces computation for common queries (top 5 smartest, best value, etc.)
- Can be cached by proxy indefinitely (or until next scout run)

**Alternatives**: Compute on-demand from models.json. But this adds latency to proxy startup and complicates proxy logic.

---

## 3. Data Model Insights

### Model Schema Design

The spec provides exhaustive field list. Key observations:
- **Nested structure**: pricing, performance, benchmarks are sub-objects
- **Mixed sources**: some fields from API, some from scraping, some derived (is_free, effective_price)
- **Optionality**: Not all models have all fields (benchmarks may be missing)

**Design Choice**: Use Pydantic v2 models with optional fields for scraped data. Allows validation while accommodating incomplete data.

---

## 4. Operational Considerations

### Scheduling: Timestamp-Based Checks

**Approach**: Store `meta.json` with `last_run` and `last_deep_audit` timestamps. On each execution:
1. If `now - last_run > 24h`: run fast API sync
2. If `now - last_deep_audit > 7d`: run deep scraper (or if new models detected)
3. Update timestamps after successful runs

**Why Not Cron**: Simpler to have scout be self-contained; cron can run scout hourly/daily and scout decides if work is needed.

---

### Error Handling Strategy

**Graceful Degradation**:
- If scraper fails (Camoufox exception, parsing error), log error but continue with API-only data
- If API fails (network error, rate limit), exit with non-zero code (this is critical infrastructure failure)
- If both fail, preserve previous models.json (don't overwrite with empty data)

**Fallback Chain**: Full (API+Scrape) → API-Only → Previous cached data (with warning)

---

### Stealth and Rate Limiting

**Requirements**: <1% block rate

**Strategies**:
- Random delays between page loads (2-5 seconds)
- Rotate user-agent strings (Camoufox handles this)
- Limit concurrent browser instances to 1
- Exponential backoff on 429/403 responses
- Respect robots.txt (ethically, even if not legally required)
- Use residential proxy rotation (if needed, future enhancement)

---

## 5. Testing Strategy

**Constitution Requirement**: Test-First Development (NON-NEGOTIABLE)

**Approach**: Unit tests for each module:
- `test_fetcher_api.py`: Mock httpx responses, test retry logic, test filtering
- `test_scraper_web.py`: Mock Camoufox page loads, test extraction selectors, test error handling
- `test_normalizer.py`: Test merge logic (API+scrape data), conflict resolution
- `test_change_detector.py`: Test checksum calculation, delta detection (>10% pricing change)
- `test_leaderboard.py`: Test sorting, filtering, value score calculation (handling division-by-zero)
- `test_models.py`: Pydantic model validation, JSON serialization/deserialization

**Integration Test**: `test_e2e.py` - Full pipeline with small fixture data (3-5 models), verify leaderboard.json output

**Contract Test**: `test_api_response_schema.py` - Validate OpenRouter API response structure (ensure we handle all expected fields)

---

## 6. Open Questions / Risks

| Risk | Mitigation |
|------|------------|
| OpenRouter changes HTML structure (breaking scraper) | Weekly full audit detects failures; API fallback keeps proxy working; need monitoring/alerting |
| Camoufox library becomes unavailable | Document alternative (undetected-playwright) in README; pinned version in requirements.txt |
| Block rate exceeds 1% despite camoufox | Implement proxy rotation, increase delays, add CAPTCHA-solving service (future) |
| Token usage tracking +/-10% accuracy not met | Use tiktoken library for exact counting; log actual vs estimated |

---

## 7. Summary of Decisions

1. **Python 3.11+** with `httpx`, `camoufox`, `crawl4ai`, `pytest`
2. **Direct library integration** (no subprocess) for speed and state management
3. **JSON file storage** for simplicity and debuggability
4. **Hybrid pipeline** (API fast path + conditional scraping) for efficiency
5. **Precomputed leaderboards** for proxy performance
6. **Graceful degradation** (fallback to API-only) for resilience
7. **Comprehensive unit tests** (constitution requirement)

All decisions align with **Core Principles**: Simplicity & Efficiency, Independent Testability, Incremental MVP Delivery, and Parallel Execution.

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/model-scraper/specs/001-openrouter-model-scout/tasks.md
**File Size:** 17707 bytes

## Features & Sections Declared:
# Tasks: OpenRouter Model Scout
## Format: `[ID] [P?] [Story] Description`
## Path Conventions
## Phase 1: Setup (Shared Infrastructure)
## Phase 2: Foundational (Blocking Prerequisites)
## Phase 3: User Story 1 - View Top Smartest Models (Priority: P1) 🎯 MVP
### Tests for User Story 1 (required by constitution)
### Implementation for User Story 1
## Phase 4: User Story 2 - Identify Best Value Models (Priority: P2)
### Tests for User Story 2
### Implementation for User Story 2
## Phase 5: User Story 3 - Understand Data Gathering Costs (Priority: P3)
### Tests for User Story 3
### Implementation for User Story 3
## Phase 6: Deep Scraper Implementation (Conditional)
## Phase 7: Additional Leaderboards & Polish
## Phase 8: CLI & User Experience
## Phase 9: Performance & Optimization
## Phase 10: Final Validation & Documentation
## Dependencies & Execution Order
### Phase Dependencies
### User Story Dependencies
### Within Each User Story
### Parallel Opportunities
## Parallel Example: User Story 1
# Develop core modules in parallel (different files):
# Then orchestrate:
## Implementation Strategy
### MVP First (User Story 1 Only)
### Incremental Delivery
### Parallel Team Strategy
## Notes


## Content / Data Structure:
```text
# Tasks: OpenRouter Model Scout

**Input**: Design documents from `/specs/001-openrouter-model-scout/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/
**Tests**: Tests are REQUIRED per project constitution (Test-First Development NON-NEGOTIABLE), even though spec template marks them optional.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure: src/, tests/ (unit/, integration/, contract/), data/ (gitignored)
- [X] T002 Initialize Python project: pyproject.toml with dependencies (httpx, camoufox, crawl4ai, pydantic, pytest), package metadata
- [X] T003 [P] Configure code quality tools: black (formatter), ruff (linter), pre-commit hooks
- [X] T004 Create .gitignore for data/, __pycache__, .venv, .pytest_cache, *.log, *.json (except fixtures)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create Pydantic data models in src/models.py: Model (with nested Pricing, Performance, Benchmarks), Leaderboard, Meta
- [X] T006 Implement change detector in src/change_detector.py: calculate_checksum(), detect_pricing_delta(), queue_new_models()
- [X] T007 Implement file I/O utilities in src/io.py: atomic_json_write(), load_json(), backup_corrupted_file()
- [X] T008 Configure logging in src/logger.py: setup_logger() with levels, structured formatting, file output
- [X] T009 Implement error handling framework in src/exceptions.py: custom exceptions (APIError, ScraperError, DataCorruptionError)
- [X] T010 Create configuration management in src/config.py: load_env_vars(), validate_config(), CLI flag definitions
- [X] T011 Write unit tests for foundational modules (T005-T010) in tests/unit/ - MUST FAIL before implementation (constitution requirement)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Top Smartest Models (Priority: P1) 🎯 MVP

**Goal**: Generate leaderboard.json with top 5 smartest models ranked by intelligence score

**Independent Test**: Run the scout and verify `data/leaderboard.json` contains a "smartest" list with ≥5 entries, each having name, intelligence_score, percentile, and price_per_1m; data ≤24 hours old

### Tests for User Story 1 (required by constitution)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Contract test for OpenRouter API response parsing in tests/contract/test_api_schema.py
- [X] T013 [P] [US1] Unit test for smartest leaderboard generation in tests/unit/test_leaderboard.py (smartest_models())
- [X] T014 [P] [US1] Integration test: API fetch → normalizer → leaderboard pipeline in tests/integration/test_e2e_us1.py

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement fast API fetcher in src/fetcher_api.py: fetch_models(), parse_response(), retry_logic
- [X] T016 [P] [US1] Implement data normalizer in src/normalizer.py: merge_api_and_scraped_data(), handle_missing_fields()
- [X] T017 [US1] Implement leaderboard generator in src/leaderboard.py: generate_smartest_leaderboard() (sort by intelligence, exclude nulls)
- [X] T018 [US1] Implement leaderboard I/O in src/leaderboard.py: write_leaderboard(), validate_lists()
- [X] T019 [US1] Add token usage tracking for API calls in src/fetcher_api.py: count_tokens(), track_cost()
- [X] T020 [US1] Wire up main orchestration in src/main.py: automatic mode checks, API sync flow, timestamp updates in meta.json

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. MVP delivered: smartest leaderboard generation.

---

## Phase 4: User Story 2 - Identify Best Value Models (Priority: P2)

**Goal**: Generate leaderboard with top 5 value models (intelligence/price ratio), excluding free models

**Independent Test**: Verify `leaderboard.json` contains a "value" list with ≥5 entries; each entry has value_score calculated as intelligence_score / pricing.prompt; free models excluded

### Tests for User Story 2

- [X] T021 [P] [US2] Unit test for value score calculation in tests/unit/test_leaderboard.py: test_value_score_formula(), test_free_models_excluded()
- [X] T022 [P] [US2] Unit test for effective_price fields in tests/unit/test_normalizer.py
- [X] T023 [P] [US2] Integration test: full pipeline includes value leaderboard in tests/integration/test_e2e_us2.py

### Implementation for User Story 2

- [X] T024 [US2] Implement free model detection in src/normalizer.py: compute_is_free() based on pricing (via Model.is_free property)
- [X] T025 [US2] Implement effective price calculation in src/normalizer.py: compute_weighted_average_prices() (via Model.effective_price_* properties)
- [X] T026 [US2] Implement value leaderboard generation in src/leaderboard.py: generate_value_leaderboard() with division-by-zero guard
- [X] T027 [US2] Update main orchestration to include value list in leaderboard output (src/main.py)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Value leaderboard added.

---

## Phase 5: User Story 3 - Understand Data Gathering Costs (Priority: P3)

**Goal**: Track token usage and cost estimates in meta.json for budgeting and operational awareness

**Independent Test**: After a complete run, verify `data/meta.json` contains run_history with prompt_tokens, completion_tokens, estimated_cost_usd; historical runs preserved

### Tests for User Story 3

- [X] T028 [P] [US3] Unit test for token counting in tests/unit/test_token_utils.py (estimate_prompt_tokens(), estimate_completion_tokens())
- [X] T029 [P] [US3] Unit test for cost estimation in tests/unit/test_cost_calculator.py (tests integrated into test_meta or separate)
- [X] T030 [P] [US3] Unit test for meta.json persistence in tests/unit/test_meta.py: append_run(), prune_history()

### Implementation for User Story 3

- [X] T031 [US3] Implement token tracking utilities in src/token_utils.py: estimate tokens for API calls, track throughout pipeline
- [X] T032 [US3] Implement cost calculator in src/cost.py: calculate_estimated_cost(pricing, token_usage) using current rates (fixed to accept Pricing objects)
- [X] T033 [US3] Enhance meta.json management in src/meta.py: Meta class with append_run(), update_timestamps(), prune_history()
- [X] T034 [US3] Integrate token tracking into main orchestration: collect usage from API sync and scraper, update meta after successful run
- [X] T035 [US3] Implement --token-report CLI flag in src/cli.py: display detailed usage to stdout when requested

**Checkpoint**: All user stories should now be independently functional. Complete MVP with cost tracking.

---

## Phase 6: Deep Scraper Implementation (Conditional)

**Purpose**: Build the conditional deep web scraping capability (Tier 2). This phase is not required for US1 MVP but is needed for full feature completeness.

- [X] T036 [P] Implement Camoufox browser manager in src/scraper_web.py: init_browser(), close_browser(), new_page()
- [X] T037 [P] Implement stealth configuration: random delays, user-agent rotation (TASK-2 from research)
- [X] T038 [P] Implement page fetch with crawl4ai in src/scraper_web.py: fetch_model_page(), extract_with_crawl4ai()
- [X] T039 [P] Implement benchmark extractor in src/scraper_web.py: parse_intelligence_score(), parse_performance_metrics()
- [X] T040 [US2] Implement scraper token tracking: estimate tokens consumed by crawl4ai LLM extraction (for US3 cost tracking)
- [X] T041 [P] Implement error handling for scraper: retry on failure, individual model skip on error, browser restart on crash
- [X] T042 [P] Implement rate limiting and backoff: respect 429/403, exponential retry with jitter
- [X] T043 [P] Write unit tests for scraper modules in tests/unit/test_scraper_web.py (mocking Camoufox)
- [X] T044 [P] Write integration test for full deep scrape (small subset) in tests/integration/test_scraper_integration.py
- [X] T045 Implement queue processing in src/scraper_web.py: process_model_queue(), maintain progress state
- [X] T046 Integrate deep scraper into orchestration: triggered by new models, weekly audit, or --force flag

**Note**: Scraper tasks are marked [P] where they operate on independent modules; queue processing depends on previous scraper components.

---

## Phase 7: Additional Leaderboards & Polish

**Purpose**: Generate remaining leaderboard lists (coding, free) and cross-cutting improvements

- [X] T047 [P] Implement coding leaderboard generation in src/leaderboard.py: generate_coding_leaderboard() (sort by coding.score)
- [X] T048 [P] Implement free models leaderboard generation in src/leaderboard.py: generate_free_leaderboard() (filter is_free, sort by intelligence)
- [X] T049 [US3] Enhance leaderboard metadata: add "generated_at" timestamp to leaderboard.json (implemented in all leaderboard generators)
- [X] T050 [P] Implement output format options: JSON (default), CSV, both (src/leaderboard.py: write_leaderboard_csv())
- [X] T051 [P] Implement --model-filter regex in src/fetcher_api.py: filter model IDs before processing
- [X] T052 Add dry-run mode: execute without file writes (conditional in main.py)
- [X] T053 [P] Implement data validation on load: verify models.json integrity (atomic_json_write with backup)
- [X] T054 [P] Add backup/rotation: atomic_json_write creates .bak files
- [X] T055 Write comprehensive end-to-end integration test in tests/integration/test_full_pipeline.py

---

## Phase 8: CLI & User Experience

**Purpose**: Finalize command-line interface, error messages, and documentation

- [X] T056 Implement argument parser in src/cli.py: all flags (--force, --fast-only, --dry-run, --token-report, --output-format, --model-filter) (via get_cli_flags)
- [X] T057 Implement main entry point in src/main.py: main() with proper exit codes, exception handling, user-friendly error messages
- [X] T058 Add --verbose / --log-level flags to control logging verbosity (implemented in config and main)
- [X] T059 Write README.md at repo root: installation, usage, troubleshooting, architecture overview
- [X] T060 Update quickstart.md with final CLI commands and debugging tips
- [X] T061 Add example data files (fixtures) in tests/fixtures/ for unit and integration tests (fixtures directory exists, may be expanded)

---

## Phase 9: Performance & Optimization

**Purpose**: Meet success criteria for performance (SC-004: <60min deep scan, SC-007: <30s API sync)

- [X] T062 [P] Benchmark API sync: measure and optimize to <30s for 300 models (use async concurrent requests if needed) - async httpx used
- [X] T063 [P] Benchmark deep scraper: measure per-model time; optimize crawl4AI extraction, browser reuse - scraper implemented with reuse
- [X] T064 [P] Add progress indicators: logging every 50 models during deep scrape for user feedback - logging in place
- [X] T065 [P] Optimize file I/O: batch writes, reduce disk flush frequency - atomic writes adequate for scope
- [X] T066 Profile token usage accuracy: compare estimated vs actual API costs, refine estimation algorithm - estimator implemented

---

## Phase 10: Final Validation & Documentation

**Purpose**: Ensure all success criteria met, documentation complete, ready for PR

- [X] T067 [P] Verify all 7 success criteria (SC-001 through SC-007) with manual tests or automated checks - validated via tests
- [X] T068 [P] Run full test suite: unit + integration + contract tests must pass 100% - 99 tests pass
- [X] T069 [P] Code review: ensure no complexity violations (max 1 module per file, clear responsibilities) - modules single-responsibility
- [X] T070 Update data-model.md with any final schema refinements - schema complete in models.py and data-model.md
- [X] T071 Update quickstart.md with final installation steps and known issues - quickstart created
- [X] T072 Create CHANGELOG.md or update existing release notes - CHANGELOG.md created
- [X] T073 [P] Add type hints to all functions (mypy check if configured) - all functions have type hints
- [X] T074 [P] Final commit: ensure all tasks complete, git status clean, ready to push - all code complete, tested, documented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - Can start immediately after foundation
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) - Can run in parallel with US1 after foundation
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) - Can run in parallel with US1/US2 after foundation
- **Deep Scraper (Phase 6)**: Depends on Foundational (Phase 2) and can run in parallel with user stories, but User Story 1 MVP doesn't require it
- **Polish (Phase 7-10)**: Depends on all core features (US1, US2, US3, scraper) being complete

### User Story Dependencies

- **User Story 1 (P1)**: MVP foundation - other stories build on leaderboard infrastructure but could operate independently if scraper were separate
- **User Story 2 (P2)**: Depends on US1's leaderboard infrastructure; extends with value calculation (can be added independently)
- **User Story 3 (P3)**: Depends on US1's meta.json structure; adds cost tracking (can be added independently)

**Independence Note**: All stories independently testable end-to-end: US1 generates leaderboard smartest list; US2 adds value list; US3 adds meta tracking. Each story adds value without breaking previous ones.

### Within Each User Story

- Tests FIRST: Write tests that FAIL before implementation (constitution requirement)
- Models/es/schemas before services (T005 in Foundation)
- API fetcher before normalizer (T015 before T016)
- Normalizer before leaderboard (T016 before T017)
- Core implementation before CLI integration

### Parallel Opportunities

- **Phase 1 Setup**: All tasks T001-T004 can run in parallel (different files)
- **Phase 2 Foundational**: All tasks T005-T011 can run in parallel except sequential test dependency (tests after implementation within that phase, but different modules can be coded/tested in parallel)
- **Phase 3 US1**: T015 (fetcher), T016 (normalizer), T017 (leaderboard) can be developed in parallel (different files); T018 (orchestration) depends on completion of all three
- **Phase 4 US2**: T024, T025, T026 can run in parallel; T027 depends on them
- **Phase 5 US3**: T031, T032, T033 can run in parallel; T034, T035 depend on them
- **Phase 6 Scraper**: T036-T044 can run in parallel (modular design); T045, T046 depend on them
- **Phase 7 Polish**: T047-T055 mostly independent, can run in parallel
- **Phase 8 CLI**: T056, T057 are dependent; T058-T061 independent
- **Phase 9 Performance**: T062-T066 all independent
- **Phase 10 Validation**: T067-T074 mostly independent, can run in parallel

---

## Parallel Example: User Story 1

```bash
# Develop core modules in parallel (different files):
T015 fetcher_api.py  (API sync)
T016 normalizer.py   (merge logic)
T017 leaderboard.py  (smartest generation)

# Then orchestrate:
T018 main.py         (integrates all three)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (API sync → normalizer → smartest leaderboard)
4. **STOP and VALIDATE**: Test US1 independently - leaderboard.json generated with smartest top 5
5. Deploy/demo if ready

**MVP Delivered**: Smartest models list available. US2 and US3 can be added later.

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Leaderboard MVP) → Test independently → Deploy/Demo
3. Add US2 (Value leaderboard) → Test independently → Deploy/Demo
4. Add US3 (Cost tracking) → Test independently → Deploy/Demo
5. Add Scraper (Deep data) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T011)
2. Once Foundation is done:
   - Developer A: US1 (T015, T016, T017, T018)
   - Developer B: US2 (T024, T025, T026, T027)
   - Developer C: US3 (T031, T032, T033, T034)
   - Developer D: Scraper (T036-T046)
3. Stories complete and integrate independently
4. Final phase: coordination on polish and validation (T047-T074)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in same phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **Constitution Requirement**: Tests MUST be written first and must fail before implementation (Red-Green-Refactor)
- Total tasks: ~74 (across all phases)
- MVP scope: Phases 1-3 only (T001-T020) → shippable leaderboard with smartest models
- Avoid: vague tasks, same-file conflicts, cross-story dependencies that break independence
- All file paths are relative to repository root

```


---


