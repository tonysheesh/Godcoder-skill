#!/usr/bin/env python3
"""
skill_scanner.py — Discovers installed skills across /mnt/skills/{user,public,examples}
and scores relevance to a given task description using keyword matching against
each skill's frontmatter description.

Usage:
  python tools/skill_scanner.py scan --task "build a slide deck about Q3 sales"
  python tools/skill_scanner.py list
"""

import argparse
import json
import re
from pathlib import Path


SKILL_ROOTS = [
    Path("/mnt/skills/user"),
    Path("/mnt/skills/public"),
    Path("/mnt/skills/examples"),
]

# Always-on skills regardless of task content (run on every message)
ALWAYS_ON = {"meta-skills-aio", "superpowers-aio"}

STOPWORDS = {
    "the", "a", "an", "of", "to", "for", "and", "or", "in", "on", "with",
    "this", "that", "is", "are", "be", "it", "as", "at", "by", "from",
}


def parse_frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text(errors="replace")
    match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {"name": skill_md.parent.name, "description": ""}
    fm = match.group(1)
    name_match = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
    desc_match = re.search(r"^description:\s*>?\s*\n((?:^\s+.+\n?)+)", fm, re.MULTILINE)
    if not desc_match:
        desc_match = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
        desc = desc_match.group(1) if desc_match else ""
    else:
        desc = " ".join(line.strip() for line in desc_match.group(1).splitlines())
    name = name_match.group(1).strip() if name_match else skill_md.parent.name
    return {"name": name, "description": desc}


def discover_skills() -> list:
    found = []
    for root in SKILL_ROOTS:
        if not root.exists():
            continue
        for entry in root.iterdir():
            if not entry.is_dir():
                continue
            skill_md = entry / "SKILL.md"
            if not skill_md.exists():
                continue
            meta = parse_frontmatter(skill_md)
            found.append({
                "name": meta["name"],
                "dir": entry.name,
                "path": str(skill_md),
                "description": meta["description"],
                "root": str(root),
            })
    return found


def tokenize(text: str) -> set:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def score_relevance(task: str, skill: dict) -> float:
    if skill["dir"] == "godcoder":
        return 0.0  # never load self

    if skill["dir"] in ALWAYS_ON:
        return 2.0

    task_tokens = tokenize(task)
    desc_tokens = tokenize(skill["description"])
    overlap = task_tokens & desc_tokens

    if not overlap:
        return 0.0

    # Score scales with overlap size, capped
    score = min(2.0, 0.5 + len(overlap) * 0.3)
    return round(score, 2)


def cmd_scan(args):
    skills = discover_skills()
    scored = []
    for s in skills:
        relevance = score_relevance(args.task, s)
        if relevance > 0:
            scored.append({
                "name": s["name"],
                "dir": s["dir"],
                "path": s["path"],
                "relevance": relevance,
                "reason": "always-on" if s["dir"] in ALWAYS_ON else "keyword-match",
            })
    scored.sort(key=lambda x: x["relevance"], reverse=True)
    print(json.dumps({
        "task": args.task,
        "relevant_skills": scored,
        "load_threshold": 1.0,
        "should_load": [s for s in scored if s["relevance"] >= 1.0],
    }, indent=2))


def cmd_list(args):
    skills = discover_skills()
    print(json.dumps(skills, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Godcoder skill scanner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan")
    p_scan.add_argument("--task", required=True)

    sub.add_parser("list")

    args = parser.parse_args()
    if args.cmd == "scan":
        cmd_scan(args)
    else:
        cmd_list(args)


if __name__ == "__main__":
    main()
