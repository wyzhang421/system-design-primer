#!/usr/bin/env python3
import sys, json, os, pathlib, datetime, re
from collections import Counter, defaultdict

# Opt-out if needed
if os.getenv("CLAUDE_SUMMARY_DISABLE") == "1":
    sys.exit(0)

LOG_ROOT = pathlib.Path(os.getenv(
    "CLAUDE_LOG_DIR",
    "~/Library/Application Support/ClaudeLogs"
)).expanduser()
SUMMARY_DIR = LOG_ROOT / "summaries"
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

MAX_TAIL_BYTES = int(os.getenv("CLAUDE_SUMMARY_TAIL_BYTES", "300000"))  # ~300KB
MAX_RECENT_MSGS = int(os.getenv("CLAUDE_SUMMARY_RECENT_MSGS", "30"))
MAX_RECENT_USER_PROMPTS = int(os.getenv("CLAUDE_SUMMARY_RECENT_USER_PROMPTS", "5"))

ROLE_KEYS = ("role", "speaker", "type")
TEXT_KEYS = ("text", "content", "message", "assistant_response", "user_input")

FAIL_PATTERNS = [
    r"\b(i\s+couldn'?t|failed|unable to|did not succeed|error|exception|stack trace)\b",
    r"\b(build|compile|test|run|deploy|install|start)\b.*\b(failed|error)\b",
]

TODO_PATTERNS = [
    r"\b(next steps?|todo|follow[-\s]?up|action items?)\b",
    r"^[-*]\s*(\[ \]|\[x\])?.*",
]

def now_iso():
    return datetime.datetime.now().astimezone().isoformat()

def read_tail(path: pathlib.Path, max_bytes: int) -> list[dict]:
    """Read the tail of a JSONL transcript file and return parsed dicts."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - max_bytes))
            tail = f.read().decode("utf-8", "ignore")
        objs = []
        for line in tail.splitlines():
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                objs.append(json.loads(line))
            except Exception:
                # ignore malformed lines
                pass
        return objs[-MAX_RECENT_MSGS:]
    except Exception:
        return []

def extract_text(d: dict) -> str:
    chunks = []
    for k in TEXT_KEYS:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            chunks.append(v)
    # Handle Claude tool message shapes like {"content":[{"type":"text","text":"..."}]}
    if not chunks and isinstance(d.get("content"), list):
        for c in d["content"]:
            if isinstance(c, dict) and c.get("type") == "text" and isinstance(c.get("text"), str):
                chunks.append(c["text"])
    return "\n".join(chunks).strip()

def role_of(d: dict) -> str:
    # normalize roles
    role = ""
    for k in ROLE_KEYS:
        v = d.get(k)
        if isinstance(v, str):
            role = v.lower()
            break
    if not role and "tool_name" in d:
        role = "tool"
    if role in ("assistant", "claude"):
        return "assistant"
    if role in ("user"):
        return "user"
    if role == "tool":
        return "tool"
    return role or d.get("hook_event_name", "")

def detect_failures(text: str) -> bool:
    for pat in FAIL_PATTERNS:
        if re.search(pat, text, flags=re.I):
            return True
    return False

def collect_todos(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        for pat in TODO_PATTERNS:
            if re.search(pat, line, flags=re.I):
                lines.append(line.strip())
                break
    # de-dup while preserving order
    seen = set(); out = []
    for l in lines:
        if l.lower() in seen: continue
        seen.add(l.lower()); out.append(l)
    return out[:10]

def summarize(transcript_entries: list[dict]) -> dict:
    """Produce a lightweight summary dict."""
    recent_user_prompts = []
    tool_runs = []
    assistant_snippets = []
    failures = []
    roles_counter = Counter()
    tools_counter = Counter()
    todos = []

    for e in transcript_entries:
        r = role_of(e)
        roles_counter[r] += 1
        text = extract_text(e)

        if r == "user" and text:
            recent_user_prompts.append(text)

        if r == "assistant" and text:
            assistant_snippets.append(text)
            if detect_failures(text):
                failures.append(("assistant", text[:400]))

        # Tool events (heuristics)
        tname = e.get("tool_name")
        if tname:
            tools_counter[tname] += 1
            tool_entry = {
                "tool": tname,
                "input": e.get("tool_input"),
                "success": (e.get("tool_response") or {}).get("success")
            }
            # Grab stderr-ish fields for context
            tr = e.get("tool_response") or {}
            err_bits = []
            for k in ("stderr", "error", "message", "reason", "details"):
                v = tr.get(k)
                if isinstance(v, str) and v.strip():
                    err_bits.append(f"{k}: {v}")
            if err_bits:
                tool_entry["error"] = "\n".join(err_bits)[:400]
                failures.append(("tool", tool_entry["error"]))
            tool_runs.append(tool_entry)

    # Find "Next steps / TODO" signals from assistant messages
    for snip in assistant_snippets[-8:]:
        todos.extend(collect_todos(snip))

    return {
        "roles": dict(roles_counter),
        "tools_used": dict(tools_counter),
        "recent_user_prompts": recent_user_prompts[-MAX_RECENT_USER_PROMPTS:],
        "tool_runs": tool_runs[-10:],
        "failures": failures[-10:],
        "todos": todos[:10],
    }

def write_markdown(summary: dict, session_id: str | None, cwd: str | None):
    ts = now_iso()
    date = ts[:10]  # YYYY-MM-DD
    out_dir = SUMMARY_DIR / date
    out_dir.mkdir(parents=True, exist_ok=True)

    # One rolling daily file; also tag session for grep-ability
    md_path = out_dir / f"summary-{date}.md"

    # Compose markdown
    lines = []
    lines.append(f"## Summary @ {ts}")
    if session_id:
        lines.append(f"- **Session:** `{session_id}`")
    if cwd:
        lines.append(f"- **CWD:** `{cwd}`")

    # Roles
    if summary.get("roles"):
        roles_str = ", ".join(f"{k}:{v}" for k, v in summary["roles"].items())
        lines.append(f"- **Message roles seen:** {roles_str}")

    # Tools
    if summary.get("tools_used"):
        tools_str = ", ".join(f"{k}:{v}" for k, v in summary["tools_used"].items())
        lines.append(f"- **Tools used:** {tools_str}")

    # Prompts
    rups = summary.get("recent_user_prompts") or []
    if rups:
        lines.append("\n**Recent user prompts:**")
        for p in rups:
            p1 = p.strip().replace("\n", " ")[:300]
            lines.append(f"- {p1}")

    # Tool runs
    trs = summary.get("tool_runs") or []
    if trs:
        lines.append("\n**Recent tool runs:**")
        for t in trs:
            line = f"- `{t.get('tool')}` success={t.get('success')}"
            if t.get("error"):
                line += f" — error: {t['error']}"
            lines.append(line)

    # Failures
    fails = summary.get("failures") or []
    if fails:
        lines.append("\n**Failure signals:**")
        for src, snippet in fails:
            snippet1 = (snippet or "").replace("\n", " ")[:300]
            lines.append(f"- ({src}) {snippet1}")

    # Todos
    todos = summary.get("todos") or []
    if todos:
        lines.append("\n**Next steps / TODOs (heuristic):**")
        for t in todos:
            lines.append(f"- {t}")

    lines.append("")  # trailing newline

    with open(md_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    try:
        event = json.load(sys.stdin)  # Stop event payload
    except Exception:
        sys.exit(0)

    if event.get("hook_event_name") != "Stop":
        sys.exit(0)

    transcript_path = event.get("transcript_path")
    session_id = event.get("session_id")
    cwd = event.get("cwd")

    if not transcript_path:
        # Nothing to summarize, but don't block
        sys.exit(0)

    tr_path = pathlib.Path(transcript_path).expanduser()
    entries = read_tail(tr_path, MAX_TAIL_BYTES)
    if not entries:
        sys.exit(0)

    summary = summarize(entries)
    write_markdown(summary, session_id, cwd)

    # Never block Claude Code
    sys.exit(0)

if __name__ == "__main__":
    main()