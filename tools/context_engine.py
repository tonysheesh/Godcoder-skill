#!/usr/bin/env python3
"""
context_engine.py — Optional context engine client.
Wraps the Go service at http://127.0.0.1:8106 (Qdrant + FalkorDB + BM25).
Falls back gracefully if the engine is offline.

Usage:
  python tools/context_engine.py search --query "..." [--limit 10]
  python tools/context_engine.py graph  --symbol "MyFunc" [--depth 2]
  python tools/context_engine.py index  --root PATH      (trigger re-index)
  python tools/context_engine.py status
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


ENGINE_URL = "http://127.0.0.1:8106"
TIMEOUT = 5


def request(method: str, path: str, body: dict = None) -> dict:
    url = f"{ENGINE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"} if data else {}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError:
        return {"error": "context_engine_offline", "fallback": True}
    except Exception as e:
        return {"error": str(e), "fallback": True}


def cmd_status(args):
    result = request("GET", "/health")
    if result.get("fallback"):
        print(json.dumps({"status": "offline", "message": "Context engine not running. Start with: docker compose up -d"}))
    else:
        print(json.dumps({"status": "online", "detail": result}))


def cmd_search(args):
    result = request("POST", "/search", {
        "query": args.query,
        "limit": args.limit,
        "modes": ["semantic", "bm25"],
    })
    if result.get("fallback"):
        print(json.dumps({"results": [], "note": "Context engine offline — falling back to text_search tool"}))
    else:
        print(json.dumps(result, indent=2))


def cmd_graph(args):
    result = request("POST", "/graph", {
        "symbol": args.symbol,
        "depth": args.depth,
    })
    if result.get("fallback"):
        print(json.dumps({"nodes": [], "edges": [], "note": "Context engine offline"}))
    else:
        print(json.dumps(result, indent=2))


def cmd_index(args):
    result = request("POST", "/index/sync-complete", {
        "root": str(Path(args.root).resolve()),
    })
    if result.get("fallback"):
        print(json.dumps({"status": "error", "message": "Context engine offline"}))
    else:
        print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Godcoder context engine client")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_status = sub.add_parser("status")

    p_search = sub.add_parser("search")
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--limit", type=int, default=10)

    p_graph = sub.add_parser("graph")
    p_graph.add_argument("--symbol", required=True)
    p_graph.add_argument("--depth", type=int, default=2)

    p_index = sub.add_parser("index")
    p_index.add_argument("--root", default=".")

    args = parser.parse_args()
    dispatch = {
        "status": cmd_status,
        "search": cmd_search,
        "graph": cmd_graph,
        "index": cmd_index,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
