#!/usr/bin/env python3
"""
checkpoint.py — Godcoder file checkpoint manager.
Snapshot files before edits; restore on failure; diff between states.
Checkpoints are stored outside the sandbox in ~/.godcoder/checkpoints/.

Usage:
  python tools/checkpoint.py save   --files path1,path2 [--label "my label"]
  python tools/checkpoint.py restore --id CHECKPOINT_ID
  python tools/checkpoint.py diff    --id CHECKPOINT_ID
  python tools/checkpoint.py list    [--limit 20]
  python tools/checkpoint.py delete  --id CHECKPOINT_ID
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import difflib
from datetime import datetime, timezone
from pathlib import Path


CHECKPOINT_DIR = Path.home() / ".godcoder" / "checkpoints"


def checkpoint_id(label: str = "") -> str:
    ts = datetime.now(timezone.utc).isoformat()
    raw = f"{ts}-{label}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def meta_path(ckpt_id: str) -> Path:
    return CHECKPOINT_DIR / ckpt_id / "meta.json"


def cmd_save(args):
    files = [Path(f.strip()) for f in args.files.split(",") if f.strip()]
    label = args.label or ""
    ckpt_id = checkpoint_id(label)
    ckpt_dir = CHECKPOINT_DIR / ckpt_id
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for path in files:
        path = path.resolve()
        if not path.exists():
            saved.append({"path": str(path), "status": "not_found"})
            continue
        # Flatten path to safe filename
        safe = str(path).replace("/", "__").replace("\\", "__").replace(":", "_")
        dest = ckpt_dir / safe
        shutil.copy2(path, dest)
        saved.append({"path": str(path), "stored_as": safe, "status": "saved"})

    meta = {
        "id": ckpt_id,
        "label": label,
        "ts": datetime.now(timezone.utc).isoformat(),
        "files": saved,
    }
    meta_path(ckpt_id).write_text(json.dumps(meta, indent=2))

    print(json.dumps({"checkpoint_id": ckpt_id, "files_saved": len([s for s in saved if s["status"] == "saved"])}))


def cmd_restore(args):
    ckpt_id = args.id
    ckpt_dir = CHECKPOINT_DIR / ckpt_id
    mp = meta_path(ckpt_id)

    if not mp.exists():
        print(json.dumps({"error": f"Checkpoint {ckpt_id} not found"}))
        sys.exit(1)

    meta = json.loads(mp.read_text())
    restored = []
    for entry in meta["files"]:
        if entry["status"] != "saved":
            continue
        src = ckpt_dir / entry["stored_as"]
        dest = Path(entry["path"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        restored.append(entry["path"])

    print(json.dumps({"checkpoint_id": ckpt_id, "restored": restored}))


def cmd_diff(args):
    ckpt_id = args.id
    ckpt_dir = CHECKPOINT_DIR / ckpt_id
    mp = meta_path(ckpt_id)

    if not mp.exists():
        print(json.dumps({"error": f"Checkpoint {ckpt_id} not found"}))
        sys.exit(1)

    meta = json.loads(mp.read_text())
    diffs = []
    for entry in meta["files"]:
        if entry["status"] != "saved":
            continue
        stored = (ckpt_dir / entry["stored_as"]).read_text(errors="replace").splitlines(keepends=True)
        current_path = Path(entry["path"])
        if not current_path.exists():
            diffs.append({"file": entry["path"], "diff": "FILE DELETED"})
            continue
        current = current_path.read_text(errors="replace").splitlines(keepends=True)
        diff = list(difflib.unified_diff(stored, current,
                                          fromfile=f"checkpoint/{entry['path']}",
                                          tofile=f"current/{entry['path']}"))
        diffs.append({"file": entry["path"], "diff": "".join(diff) or "NO CHANGE"})

    print(json.dumps(diffs, indent=2))


def cmd_list(args):
    if not CHECKPOINT_DIR.exists():
        print(json.dumps([]))
        return
    checkpoints = []
    for ckpt_dir in sorted(CHECKPOINT_DIR.iterdir(), reverse=True):
        mp = ckpt_dir / "meta.json"
        if not mp.exists():
            continue
        meta = json.loads(mp.read_text())
        checkpoints.append({
            "id": meta["id"],
            "label": meta.get("label", ""),
            "ts": meta["ts"],
            "file_count": len([f for f in meta["files"] if f["status"] == "saved"]),
        })
        if len(checkpoints) >= args.limit:
            break
    print(json.dumps(checkpoints, indent=2))


def cmd_delete(args):
    ckpt_dir = CHECKPOINT_DIR / args.id
    if not ckpt_dir.exists():
        print(json.dumps({"error": f"Checkpoint {args.id} not found"}))
        sys.exit(1)
    shutil.rmtree(ckpt_dir)
    print(json.dumps({"deleted": args.id}))


def main():
    parser = argparse.ArgumentParser(description="Godcoder checkpoint manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_save = sub.add_parser("save")
    p_save.add_argument("--files", required=True)
    p_save.add_argument("--label", default="")

    p_restore = sub.add_parser("restore")
    p_restore.add_argument("--id", required=True)

    p_diff = sub.add_parser("diff")
    p_diff.add_argument("--id", required=True)

    p_list = sub.add_parser("list")
    p_list.add_argument("--limit", type=int, default=20)

    p_delete = sub.add_parser("delete")
    p_delete.add_argument("--id", required=True)

    args = parser.parse_args()
    dispatch = {
        "save": cmd_save,
        "restore": cmd_restore,
        "diff": cmd_diff,
        "list": cmd_list,
        "delete": cmd_delete,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
