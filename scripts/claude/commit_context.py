"""Inject project skill documents before git commit commands."""

import json
import re
import sys
from pathlib import Path


def main() -> None:
    payload = json.load(sys.stdin)
    command = payload.get("tool_input", {}).get("command", "")
    if not re.search(r"(?:^|[;&|])\s*git\b[^;&|]*\bcommit\b", command):
        print("{}")
        return

    project_root = Path(__file__).resolve().parents[2]
    documents = []
    for path in sorted((project_root / ".claude" / "skills").glob("*.md")):
        documents.append(f"## {path.relative_to(project_root).as_posix()}\n{path.read_text(encoding='utf-8')}" )

    context = (
        "Before running git commit, apply every rule in the following project skill documents. "
        "Treat them as binding repository constraints; resolve conflicts in favor of CLAUDE.md.\n\n"
        + "\n\n".join(documents)
    )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": context}}))


if __name__ == "__main__":
    main()
