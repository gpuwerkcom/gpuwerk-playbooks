#!/usr/bin/env python3
"""Check that relative links between Markdown files in this repository resolve."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINK = re.compile(r"\]\(([^)\s]+)\)")

errors = []
for md in sorted(ROOT.rglob("*.md")):
    if ".git" in md.parts:
        continue
    text = re.sub(r"```.*?```", "", md.read_text(encoding="utf-8"), flags=re.S)
    for target in LINK.findall(text):
        if re.match(r"^(https?:|mailto:|#)", target) or target.startswith("<"):
            continue
        path = (md.parent / target.split("#", 1)[0]).resolve()
        if not path.exists():
            errors.append(f"{md.relative_to(ROOT)}: broken link {target}")

print("\n".join(errors) or "All relative links resolve.")
sys.exit(1 if errors else 0)
