"""
Claude Code CLI integration.

Handles all interactions with the Claude Code CLI tool.
"""

import subprocess
import json
import os
import time
from datetime import datetime
from typing import Tuple

from repo_agent.utils.system_logger import logger


# Claude CLI configuration
CLAUDE_PATH = "/opt/homebrew/bin/claude"
DEFAULT_MAX_TURNS = 5
DEFAULT_TIMEOUT = 300  # 5 minutes


def call_claude(
    prompt: str,
    repo_path: str,
    task_id: str,
    node: str,
    max_turns: int = DEFAULT_MAX_TURNS,
    timeout: int = DEFAULT_TIMEOUT
) -> Tuple[str, float, int]:
    """
    Call Claude Code CLI and stream output to file.
    
    Args:
        prompt: The prompt to send to Claude
        repo_path: Working directory (repository path)
        task_id: Unique task identifier for logging
        node: Node name for logging (e.g., "generator_v1")
        max_turns: Maximum tool calls before responding
        timeout: Timeout in seconds
    
    Returns:
        Tuple of (result_text, duration_seconds, exit_code)
    """
    start_time = time.time()
    
    # Output file for Claude's stream-json
    logs_dir = logger.base_log_dir
    output_file = os.path.join(logs_dir, f"{task_id}_claude.log")
    
    cmd = [
        CLAUDE_PATH,
        "-p", prompt,
        "--verbose",
        "--output-format", "stream-json",
        "--dangerously-skip-permissions",
        "--max-turns", str(max_turns)
    ]
    
    # Inherit full environment (needed for auth tokens)
    env = os.environ.copy()
    
    try:
        # Write header
        _write_header(output_file, node, repo_path, prompt)
        
        # Stream Claude output directly to file
        with open(output_file, 'a') as f:
            process = subprocess.Popen(
                cmd,
                cwd=repo_path,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            _, stderr = process.communicate(timeout=timeout)
            exit_code = process.returncode
        
        duration = time.time() - start_time
        
        # Write footer
        _write_footer(output_file, duration, exit_code)
        
        # Parse the result from the file
        output = parse_result(output_file)
        
        if exit_code != 0 and not output:
            output = f"Error: {stderr.strip()}" if stderr else "Unknown error"
        
        return output, duration, exit_code
        
    except subprocess.TimeoutExpired:
        process.kill()
        duration = time.time() - start_time
        _write_footer(output_file, duration, -1, timeout=True)
        return f"Error: Timed out after {timeout}s", duration, -1
        
    except FileNotFoundError:
        return f"Error: Claude CLI not found at {CLAUDE_PATH}", 0, -1
        
    except Exception as e:
        return f"Error: {str(e)}", time.time() - start_time, -1


def parse_result(output_file: str) -> str:
    """
    Parse the final result from stream-json output.
    
    Reads the file in reverse to find the last 'result' type event.
    """
    try:
        with open(output_file, 'r') as f:
            lines = f.readlines()
            
        for line in reversed(lines):
            line = line.strip()
            if not line or not line.startswith('{'):
                continue
            try:
                event = json.loads(line)
                if event.get("type") == "result":
                    return event.get("result", "")
            except json.JSONDecodeError:
                continue
    except Exception:
        pass
    return ""


def _write_header(output_file: str, node: str, repo_path: str, prompt: str):
    """Write log header."""
    with open(output_file, 'a') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {node.upper()}\n")
        f.write(f"Repo: {repo_path}\n")
        f.write(f"Prompt: {prompt}\n")
        f.write(f"{'='*80}\n")


def _write_footer(output_file: str, duration: float, exit_code: int, timeout: bool = False):
    """Write log footer."""
    with open(output_file, 'a') as f:
        if timeout:
            f.write(f"\n[TIMEOUT after {duration:.2f}s]\n")
        else:
            f.write(f"\n[Completed in {duration:.2f}s, exit: {exit_code}]\n")

