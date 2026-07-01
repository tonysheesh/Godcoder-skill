#!/usr/bin/env python3
"""
state.py — Read and write Godcoder session state.
State file lives at {sandbox}/state.json.

Usage:
  python tools/state.py get    --sandbox PATH [--key KEY]
  python tools/state.py set    --sandbox PATH --key KEY --value VALUE
  python tools/state.py inc    --sandbox PATH --key KEY [--by N]
  python tools/state.py append --sandbox PATH --key KEY --value VALUE
  python tools/state.py show   --sandbox PATH
"""

import argparse
import json
import sys
from pathlib import Path


def load(sandbox: Path) -> dict:
    state_file = sandbox / "state.json"
    if not state_file.exists():
        print(f"ERROR: No state.json in {sandbox}", file=sys.stderr)
        sys.exit(1)
    return json.loads(state_file.read_text())


def save(sandbox: Path, state: dict):
    (sandbox / "state.json").write_text(json.dumps(state, indent=2))


def cmd_get(args):
    state = load(Path(args.sandbox))
    if args.key:
        print(json.dumps(state.get(args.key)))
    else:
        print(json.dumps(state, indent=2))


def cmd_set(args):
    sandbox = Path(args.sandbox)
    state = load(sandbox)
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        value = args.value
    state[args.key] = value
    save(sandbox, state)
    print(json.dumps({"key": args.key, "value": value}))


def cmd_inc(args):
    sandbox = Path(args.sandbox)
    state = load(sandbox)
    by = int(args.by) if args.by else 1
    current = state.get(args.key, 0)
    state[args.key] = current + by
    save(sandbox, state)
    print(json.dumps({"key": args.key, "value": state[args.key]}))


def cmd_append(args):
    sandbox = Path(args.sandbox)
    state = load(sandbox)
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        value = args.value
    current = state.get(args.key, [])
    if not isinstance(current, list):
        current = [current]
    current.append(value)
    state[args.key] = current
    save(sandbox, state)
    print(json.dumps({"key": args.key, "length": len(current)}))


def cmd_show(args):
    state = load(Path(args.sandbox))
    print(json.dumps(state, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Godcoder state manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    for cmd in ["get", "set", "inc", "append", "show"]:
        p = sub.add_parser(cmd)
        p.add_argument("--sandbox", required=True)
        if cmd in ("set", "inc", "append"):
            p.add_argument("--key", required=True)
        if cmd in ("get",):
            p.add_argument("--key", default="")
        if cmd in ("set", "append"):
            p.add_argument("--value", required=True)
        if cmd == "inc":
            p.add_argument("--key", required=True)
            p.add_argument("--by", default="1")

    args = parser.parse_args()
    dispatch = {
        "get": cmd_get, "set": cmd_set, "inc": cmd_inc,
        "append": cmd_append, "show": cmd_show,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
