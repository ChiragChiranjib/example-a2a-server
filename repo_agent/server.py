"""
A2A Server - LangGraph + Claude Code.

Logs per task:
- tmp/logs/{task_id}.log        - System logs
- tmp/logs/{task_id}_claude.log - Claude Code thinking
"""

import os
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from repo_agent.utils.init_logs import init_log_dirs
from repo_agent.utils.system_logger import logger
from repo_agent.graph import run_review_critique


app = FastAPI(title="Repo Expert A2A Server")


class JsonRpcRequest(BaseModel):
    jsonrpc: str
    method: str
    id: str
    params: Optional[Dict[str, Any]] = None


@app.get("/.well-known/agent.json")
async def agent_card():
    """A2A Agent Card."""
    return {
        "name": "repo_expert",
        "description": "Repository expert using Claude Code with review/critique pattern",
        "version": "0.1.0",
        "protocolVersion": "0.3.0",
        "url": f"http://localhost:{os.environ.get('PORT', '8001')}",
        "capabilities": {},
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
        "skills": [{
            "id": "analyze_repo",
            "name": "Repository Analysis",
            "description": "Analyzes repositories with validation. Include 'repo_path: /path' in query.",
            "tags": ["code", "repository", "langgraph"]
        }]
    }


@app.get("/.well-known/agent-card.json")
async def agent_card_alt():
    return await agent_card()


def extract_params(text: str) -> tuple[str, str]:
    """Extract query and repo_path from message."""
    if "repo_path:" not in text.lower():
        return text.strip(), ""
    
    idx = text.lower().find("repo_path:")
    query = text[:idx].strip()
    repo_path = text[idx + len("repo_path:"):].strip().split()[0]
    
    return query or "What is this repository about?", repo_path


@app.post("/")
async def handle_jsonrpc(request: JsonRpcRequest):
    """Handle A2A requests."""
    
    if request.method != "message/send":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request.id,
            "error": {"code": -32601, "message": f"Method not found: {request.method}"}
        })
    
    # Extract message
    params = request.params or {}
    message = params.get("message", {})
    parts = message.get("parts", [])
    
    text = ""
    for part in parts:
        if "text" in part:
            text = part["text"]
            break
    
    if not text:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request.id,
            "error": {"code": -32602, "message": "No text in message"}
        })
    
    query, repo_path = extract_params(text)
    
    if not repo_path:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {
                "id": str(uuid.uuid4()),
                "kind": "task",
                "status": {"state": "failed"},
                "artifacts": [{"parts": [{"kind": "text", "text": "Include 'repo_path: /path/to/repo' in your message"}]}]
            }
        })
    
    # Generate task ID and run workflow
    task_id = str(uuid.uuid4())[:8]
    
    logger.log(task_id, "A2A Request", details={"query": query, "repo": repo_path})
    
    response = run_review_critique(query, repo_path, task_id)
    
    logger.log(task_id, "A2A Response sent")
    
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request.id,
        "result": {
            "id": task_id,
            "kind": "task",
            "status": {"state": "completed", "timestamp": datetime.now(timezone.utc).isoformat()},
            "artifacts": [{"parts": [{"kind": "text", "text": response}]}]
        }
    })


def main():
    import uvicorn
    
    logs_dir = init_log_dirs()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8001"))
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║          Repo Expert A2A Server                           ║
╠═══════════════════════════════════════════════════════════╣
║  Server: http://{host}:{port:<37}║
║  Logs:   {logs_dir:<46}║
║                                                           ║
║  Log files per task:                                      ║
║    {{task_id}}.log        - System logs                    ║
║    {{task_id}}_claude.log - Claude Code thinking           ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    uvicorn.run("repo_agent.server:app", host=host, port=port)


if __name__ == "__main__":
    main()
