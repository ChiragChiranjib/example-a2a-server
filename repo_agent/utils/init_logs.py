"""Initialize log directory."""

import os


def init_log_dirs(base_dir: str = None) -> str:
    """Create the logs directory and return its path."""
    if base_dir is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        base_dir = project_root
    
    logs_dir = os.path.join(base_dir, "tmp", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create .gitignore
    gitignore = os.path.join(base_dir, "tmp", ".gitignore")
    if not os.path.exists(gitignore):
        with open(gitignore, "w") as f:
            f.write("*\n!.gitignore\n")
    
    return logs_dir
