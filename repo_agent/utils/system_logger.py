"""
Simple Logger for Repo Agent.

- {task_id}.log        - System logs
- {task_id}_claude.log - Claude Code stream (written by graph.py)
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any


class SimpleLogger:
    
    def __init__(self, base_log_dir: str = None):
        if base_log_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            base_log_dir = os.path.join(project_root, "tmp", "logs")
        
        self.base_log_dir = base_log_dir
        os.makedirs(base_log_dir, exist_ok=True)
        
        # Console logger
        self.console = logging.getLogger('repo_agent')
        self.console.setLevel(logging.INFO)
        if not self.console.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
            self.console.addHandler(handler)
    
    def log(self, task_id: str, message: str, level: str = "INFO", details: Dict[str, Any] = None):
        """Log to system log file."""
        log_file = os.path.join(self.base_log_dir, f"{task_id}.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
            if details:
                for key, value in details.items():
                    f.write(f"  {key}: {value}\n")
        
        self.console.info(f"[{task_id}] {message}")


logger = SimpleLogger()
