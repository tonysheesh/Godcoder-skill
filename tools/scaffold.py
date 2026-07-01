#!/usr/bin/env python3
"""
scaffold.py — Godcoder task-specific sandbox initializer.
Creates harness-build/{task_id}/ for each unique task.
Run once per task at harness-build time.

Usage:
  python tools/scaffold.py --mode harness|cowork|freestyle \
                           [--task-id HASH] [--root PATH] [--task-desc "..."]
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def make_task_id(desc: str) -> str:
    return hashlib.sha1(desc.encode()).hexdigest()[:8]


def create_sandbox(mode: str, root: Path, task_id: str, task_desc: str) -> Path:
    base = root / "harness-build" / task_id
    base.mkdir(parents=True, exist_ok=True)

    # Subdirectories
    for sub in ["tools", "tests", "output", "memory"]:
        (base / sub).mkdir(exist_ok=True)

    # Harness log
    log = base / "HARNESS_LOG.md"
    if not log.exists():
        log.write_text(f"# Harness Log — {task_id}\n\n**Task:** {task_desc}\n**Mode:** {mode}\n**Started:** {datetime.now(timezone.utc).isoformat()}\n\n---\n\n")

    # Harness config / state
    state = {
        "task_id": task_id,
        "task_desc": task_desc,
        "mode": mode,
        "session_start": datetime.now(timezone.utc).isoformat(),
        "sandbox_root": str(base),
        "iteration": 0,
        "skills_loaded": [],
        "routing_weights": {},
        "avoidance_list": [],
        "success_count": 0,
        "failure_count": 0,
        "total_tokens_in": 0,
        "total_tokens_out": 0,
        "completion_condition": None,
        "status": "running",
    }
    (base / "harness.json").write_text(json.dumps(state, indent=2))

    return base


def try_open_explorer(path: Path):
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        elif sys.platform == "win32":
            subprocess.Popen(["explorer", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="harness", choices=["harness", "cowork", "freestyle"])
    parser.add_argument("--task-id", default="")
    parser.add_argument("--task-desc", default="untitled-task")
    parser.add_argument("--root", default=".")
    parser.add_argument("--open-explorer", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    task_id = args.task_id or make_task_id(args.task_desc)
    sandbox = create_sandbox(args.mode, root, task_id, args.task_desc)

    if args.open_explorer:
        try_open_explorer(sandbox)

    print(json.dumps({
        "status": "ready",
        "task_id": task_id,
        "mode": args.mode,
        "sandbox": str(sandbox),
        "log": str(sandbox / "HARNESS_LOG.md"),
        "state": str(sandbox / "harness.json"),
    }))


if __name__ == "__main__":
    main()
