#!/usr/bin/env python3
"""
memory.py — Godcoder persistent memory bridge.
Wraps a local SQLite store for log / recall / route / optimize operations.
Entries are tagged by task_id so recall can be scoped per-task or global.

Usage:
  python tools/memory.py log    --entry '{"iteration":1,...}'
  python tools/memory.py recall --query "..." [--tags harness:,tools] [--task-id ID] [--limit 10]
  python tools/memory.py route  --context "..." [--tags harness:] [--task-id ID] [--limit 5]
  python tools/memory.py optimize --iteration-result '{"outcome":"success","lesson":"..."}'
  python tools/memory.py stats  [--tags harness:] [--task-id ID]
"""

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path.home() / ".godcoder" / "memory.db"


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT NOT NULL,
            mode        TEXT NOT NULL,
            task_id     TEXT DEFAULT '',
            iteration   INTEGER NOT NULL,
            change_desc TEXT NOT NULL,
            outcome     TEXT NOT NULL,
            verification TEXT,
            lesson      TEXT NOT NULL,
            tags        TEXT NOT NULL,
            tokens_in   INTEGER DEFAULT 0,
            tokens_out  INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS routing_weights (
            pattern     TEXT PRIMARY KEY,
            weight      REAL NOT NULL DEFAULT 1.0,
            mode        TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS avoidance_list (
            pattern     TEXT NOT NULL,
            mode        TEXT NOT NULL,
            reason      TEXT,
            added_at    TEXT NOT NULL,
            PRIMARY KEY (pattern, mode)
        )
    """)
    conn.commit()
    return conn


def cmd_log(args):
    entry = json.loads(args.entry)
    conn = get_db()
    tags_str = ",".join(entry.get("tags", []))
    cost = entry.get("cost", {})
    conn.execute("""
        INSERT INTO entries (ts, mode, task_id, iteration, change_desc, outcome, verification, lesson, tags, tokens_in, tokens_out)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        entry.get("mode", "harness"),
        entry.get("task_id", ""),
        entry.get("iteration", 0),
        entry.get("change", ""),
        entry.get("outcome", "failure"),
        entry.get("verification", ""),
        entry.get("lesson", ""),
        tags_str,
        cost.get("tokens_in", 0),
        cost.get("tokens_out", 0),
    ))
    conn.commit()
    print(json.dumps({"status": "logged", "id": conn.execute("SELECT last_insert_rowid()").fetchone()[0]}))


def cmd_recall(args):
    conn = get_db()
    query = args.query.lower()
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    limit = args.limit

    sql = "SELECT * FROM entries"
    conditions = []
    params = []
    if args.task_id:
        conditions.append("task_id = ?")
        params.append(args.task_id)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY id DESC LIMIT 500"

    rows = conn.execute(sql, params).fetchall()
    words = query.split()

    results = []
    for idx, row in enumerate(rows):
        text = f"{row['change_desc']} {row['lesson']}".lower()
        row_tags = row["tags"].split(",")

        if tags and not any(t in row_tags for t in tags):
            continue

        overlap = sum(1 for w in words if w in text)
        recency_bonus = 1.0 / (1 + idx * 0.01)
        success_bonus = 0.3 if row["outcome"] == "success" else 0.0
        score = overlap + recency_bonus + success_bonus

        if overlap > 0:
            results.append({"score": score, "row": dict(row)})

    results.sort(key=lambda x: x["score"], reverse=True)
    top = [r["row"] for r in results[:limit]]
    print(json.dumps(top, indent=2, default=str))


def cmd_route(args):
    """Return ranked candidate changes based on past outcomes (global + task-scoped)."""
    conn = get_db()
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []

    sql = """
        SELECT change_desc, lesson, tags, task_id, COUNT(*) as freq
        FROM entries
        WHERE outcome = 'success'
        GROUP BY change_desc ORDER BY freq DESC LIMIT 30
    """
    successes = conn.execute(sql).fetchall()

    avoidances = conn.execute("""
        SELECT pattern, reason FROM avoidance_list WHERE mode IN (?, 'all')
    """, (tags[0].rstrip(":") if tags else "harness",)).fetchall()
    avoid_set = {row["pattern"].lower() for row in avoidances}

    candidates = []
    for row in successes:
        change = row["change_desc"]
        if any(a in change.lower() for a in avoid_set):
            continue
        row_tags = row["tags"].split(",")
        tag_match = any(t in row_tags for t in tags) if tags else True
        same_task = (row["task_id"] == args.task_id) if args.task_id else False
        confidence = min(1.0, row["freq"] / 5.0) + (0.3 if same_task else 0.0)
        candidates.append({
            "change": change,
            "lesson": row["lesson"],
            "frequency": row["freq"],
            "confidence": round(min(confidence, 1.0), 2),
            "tag_match": tag_match,
            "same_task": same_task,
        })

    candidates.sort(key=lambda c: c["confidence"], reverse=True)

    if not candidates:
        candidates = [
            {"change": "Scaffold initial structure for this task", "lesson": "First iteration: establish base structure", "frequency": 0, "confidence": 0.5},
            {"change": "Write a verification check for the core deliverable", "lesson": "Verification catches regressions before they compound", "frequency": 0, "confidence": 0.4},
            {"change": "Checkpoint before first write", "lesson": "Checkpoints enable safe iteration", "frequency": 0, "confidence": 0.4},
        ]

    print(json.dumps(candidates[:args.limit], indent=2))


def cmd_optimize(args):
    result = json.loads(args.iteration_result)
    conn = get_db()

    outcome = result.get("outcome", "failure")
    change = result.get("change", "")
    lesson = result.get("lesson", "")
    mode = result.get("mode", "harness")

    if outcome == "success":
        conn.execute("""
            INSERT INTO routing_weights (pattern, weight, mode, updated_at)
            VALUES (?, 1.2, ?, ?)
            ON CONFLICT(pattern) DO UPDATE SET
                weight = MIN(weight * 1.2, 5.0),
                updated_at = excluded.updated_at
        """, (change[:100], mode, datetime.now(timezone.utc).isoformat()))
    else:
        conn.execute("""
            INSERT INTO avoidance_list (pattern, mode, reason, added_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(pattern, mode) DO UPDATE SET
                reason = excluded.reason,
                added_at = excluded.added_at
        """, (change[:100], mode, lesson, datetime.now(timezone.utc).isoformat()))

    conn.commit()
    print(json.dumps({"status": "optimized", "outcome": outcome}))


def cmd_stats(args):
    conn = get_db()
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []

    query = "SELECT outcome, COUNT(*) as n, SUM(tokens_in + tokens_out) as tokens FROM entries WHERE 1=1"
    params = []
    if tags:
        conditions = " OR ".join("tags LIKE ?" for _ in tags)
        query += f" AND ({conditions})"
        params.extend(f"%{t}%" for t in tags)
    if args.task_id:
        query += " AND task_id = ?"
        params.append(args.task_id)
    query += " GROUP BY outcome"

    rows = conn.execute(query, params).fetchall()
    total_success = sum(r["n"] for r in rows if r["outcome"] == "success")
    total_failure = sum(r["n"] for r in rows if r["outcome"] == "failure")
    total_tokens = sum(r["tokens"] or 0 for r in rows)

    stats = {
        "success": total_success,
        "failure": total_failure,
        "total": total_success + total_failure,
        "success_rate": round(total_success / max(1, total_success + total_failure), 2),
        "total_tokens": total_tokens,
        "tokens_per_success": round(total_tokens / max(1, total_success)),
    }
    print(json.dumps(stats, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Godcoder memory bridge")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_log = sub.add_parser("log")
    p_log.add_argument("--entry", required=True)

    p_recall = sub.add_parser("recall")
    p_recall.add_argument("--query", required=True)
    p_recall.add_argument("--tags", default="")
    p_recall.add_argument("--task-id", default="")
    p_recall.add_argument("--limit", type=int, default=10)

    p_route = sub.add_parser("route")
    p_route.add_argument("--context", required=True)
    p_route.add_argument("--tags", default="")
    p_route.add_argument("--task-id", default="")
    p_route.add_argument("--limit", type=int, default=5)

    p_opt = sub.add_parser("optimize")
    p_opt.add_argument("--iteration-result", required=True)

    p_stats = sub.add_parser("stats")
    p_stats.add_argument("--tags", default="")
    p_stats.add_argument("--task-id", default="")

    args = parser.parse_args()
    dispatch = {
        "log": cmd_log, "recall": cmd_recall, "route": cmd_route,
        "optimize": cmd_optimize, "stats": cmd_stats,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
