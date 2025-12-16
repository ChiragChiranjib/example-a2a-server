# Repo Expert A2A Server

A2A server using LangGraph + Claude Code with review/critique pattern.

## Architecture

```
User Query → A2A Server → LangGraph Workflow
                              │
                              ├── Generator (Claude Code)
                              │
                              └── Validator (Claude Code)
```

## Logging

Simple per-task logging:

```
tmp/logs/
├── {task_id}.log           # System logs (workflow events)
└── {task_id}_claude.log    # Claude Code thinking/execution
```

### System Log (`{task_id}.log`)
```
[2024-12-17 14:30:22] [INFO] A2A Request
  query: What does this repo do?
  repo: /path/to/repo
[2024-12-17 14:30:22] [INFO] Generator: Starting
[2024-12-17 14:30:45] [INFO] Generator: Complete (23.1s)
[2024-12-17 14:30:45] [INFO] Validator: Starting
[2024-12-17 14:31:02] [INFO] Validator: Complete (17.2s)
[2024-12-17 14:31:02] [INFO] Workflow: Completed
```

### Claude Log (`{task_id}_claude.log`)
```
================================================================================
[2024-12-17 14:30:22] CLAUDE CODE - GENERATOR
================================================================================
Repo: /path/to/repo

PROMPT:
----------------------------------------
Examine this repository and answer: What does this repo do?
----------------------------------------

EXECUTION:

[THINKING]
Let me examine the repository structure first...

[TOOL: Read]
{
  "file_path": "README.md"
}

[THINKING]
Based on the README, this appears to be a testing framework...

OUTPUT:
----------------------------------------
This repository is a developer-centric API testing tool...
----------------------------------------

[2024-12-17 14:30:45] Completed in 23.10s (exit: 0) | Cost: $0.002345
================================================================================
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# Start server
python -m repo_agent.server

# Test with curl
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "1",
    "params": {
      "message": {
        "messageId": "msg-001",
        "role": "user",
        "parts": [{"text": "What is this repo? repo_path: /path/to/repo"}]
      }
    }
  }'
```

## Project Structure

```
repo_agent/
├── __init__.py
├── server.py      # A2A server
├── graph.py       # LangGraph workflow
└── utils/
    ├── __init__.py
    ├── init_logs.py
    └── system_logger.py
```
