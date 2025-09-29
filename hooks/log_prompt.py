#!/usr/bin/env python3
import sys, json, os, pathlib, re, datetime

# Disable logging if CLAUDE_LOG_DISABLE=1
if os.getenv("CLAUDE_LOG_DISABLE") == "1":
    sys.exit(0)

# macOS-friendly default log path; override with CLAUDE_LOG_DIR
LOG_DIR = pathlib.Path(os.getenv("CLAUDE_LOG_DIR", "~/Library/Application Support/ClaudeLogs")).expanduser()
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "prompts.jsonl"

# Rotate if larger than ~10MB
try:
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > 10 * 1024 * 1024:
        rotated = LOG_DIR / f"prompts-{datetime.date.today().isoformat()}.jsonl"
        LOG_FILE.rename(rotated)
except Exception:
    pass

def redact(text: str) -> str:
    rules = [
        (re.compile(r"(api[_-]?key|password|secret)\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{12,})['\"]?", re.I), r"\1: [REDACTED]"),
        (re.compile(r"\b\d{13,19}\b"), "[REDACTED_CARD]"),
        (re.compile(r"[\w\.-]+@[\w\.-]+\.\w+"), "[REDACTED_EMAIL]"),
    ]
    for pat, repl in rules:
        text = pat.sub(repl, text)
    return text

def main():
    try:
        data = json.load(sys.stdin)
        entry = {
            "ts": datetime.datetime.now().astimezone().isoformat(),
            "event": "UserPromptSubmit",
            "session_id": data.get("session_id"),
            "transcript_path": data.get("transcript_path"),
            "cwd": data.get("cwd"),
            "prompt": redact(data.get("prompt", "")),
        }
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        sys.exit(0)
    except Exception as e:
        print(f"[prompt-log] error: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()