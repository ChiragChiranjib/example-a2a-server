# Repo Expert A2A Server

An A2A (Agent-to-Agent) server that uses Claude Code CLI to answer questions about repositories. Features a **Review/Critique pattern** with feedback loop for validated, high-quality answers.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      A2A Protocol                           │
│                    (FastAPI Server)                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph Workflow                        │
│  ┌───────────┐      ┌───────────┐                          │
│  │ Generator │ ──▶  │ Validator │                          │
│  └───────────┘      └─────┬─────┘                          │
│        ▲                  │                                 │
│        │    INVALID/      │ VALID                          │
│        │    PARTIAL       ▼                                 │
│        └─────────────  [END]                               │
│         (with feedback)                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Claude Code CLI                           │
│              (Repository Analysis)                          │
└─────────────────────────────────────────────────────────────┘
```

## Features

- **Review/Critique Pattern**: Generator creates answer → Validator checks → Loops back with feedback if needed
- **Feedback Loop**: Up to 3 iterations to refine answers
- **Claude Code Integration**: Uses Claude CLI for deep repository analysis
- **Detailed Logging**: System logs + Claude execution traces per task

## Quick Start

```bash
# Install
make install

# Run server
make run

# Test (in another terminal)
make request
```

## Usage

### Makefile Commands

```bash
make install   # Setup venv and install deps
make run       # Start the server
make stop      # Stop the server
make test      # Check server is running
make request   # Send a sample request
make logs      # View recent logs
make clean     # Clear logs
```

### Custom Requests

```bash
# Override repo and query
make request REPO=/path/to/your/repo QUERY="explain the main function"

# Direct curl
curl -sS -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "1",
    "params": {
      "message": {
        "messageId": "m1",
        "role": "user",
        "parts": [{"text": "What does this repo do? repo_path: /path/to/repo"}]
      }
    }
  }'
```

## Project Structure

```
repo_agent/
├── __init__.py
├── server.py          # FastAPI A2A server
├── graph.py           # LangGraph workflow (generator → validator loop)
├── claude.py          # Claude Code CLI integration
└── utils/
    ├── __init__.py
    ├── init_logs.py   # Log directory setup
    └── system_logger.py

tmp/logs/              # Generated logs (gitignored)
├── {task_id}.log          # System/workflow logs
└── {task_id}_claude.log   # Claude execution traces
```

## Logging

Each request generates a unique `task_id`. Two log files are created:

| File | Contents |
|------|----------|
| `{task_id}.log` | Workflow events, timing, status |
| `{task_id}_claude.log` | Full Claude CLI output (stream-json) |

Example system log:
```
[2025-12-17 04:30:00] [INFO] A2A Request
  query: What are the probes used?
  repo: /path/to/repo
[2025-12-17 04:30:00] [INFO] Workflow: Started
[2025-12-17 04:30:15] [INFO] Generator: Done (15.2s)
[2025-12-17 04:30:30] [INFO] Validator: VALID (14.8s)
[2025-12-17 04:30:30] [INFO] Workflow: Completed (VALID after 1 iteration(s))
```

## Configuration

Edit `repo_agent/claude.py`:

```python
CLAUDE_PATH = "/opt/homebrew/bin/claude"  # Path to claude CLI
DEFAULT_MAX_TURNS = 5                      # Max tool calls per invocation
DEFAULT_TIMEOUT = 300                      # 5 minute timeout
```

## Requirements

- Python 3.10+
- Claude Code CLI (`claude`) installed and authenticated
- LangGraph

## License

MIT
