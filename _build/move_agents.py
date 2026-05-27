#!/usr/bin/env python3
"""One-time migration (Phase 2): move agent pages from /<slug>/ to /agents/<slug>/.

Agent pages drop one level deeper, so root-reaching ../ paths become ../../ — except
agent-to-agent links, which stay ../<slug>/ since every agent moves together. We
transform the template to depth 2, regenerate into agents/, delete the old root dirs,
and insert `agents/` into the agent links on every other page.
"""
import glob
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "_build")
TEMPLATE = os.path.join(BUILD, "agent_template.html")
sys.path.insert(0, BUILD)
import generate_agents  # noqa: E402

SLUGS = [a["slug"] for a in json.load(open(os.path.join(BUILD, "agents.json"), encoding="utf-8"))]
SUBDIR = generate_agents.AGENTS_SUBDIR


def deepen_template():
    """Depth-1 -> depth-2: bump every ../ to ../../, then restore agent-sibling links."""
    t = open(TEMPLATE, encoding="utf-8").read()
    if "../../" in t:
        raise SystemExit("[move] template already has ../../ — refusing to double-deepen")
    t = t.replace("../", "../../")
    for s in SLUGS:
        t = t.replace(f"../../{s}/", f"../{s}/")
    open(TEMPLATE, "w", encoding="utf-8").write(t)
    print("deepened template paths to depth 2")


def insert_agents_in_links():
    """On every non-agent page, rewrite agent links <slug>/index.html -> agents/<slug>/index.html."""
    alt = "|".join(sorted(map(re.escape, SLUGS), key=len, reverse=True))
    rx = re.compile(r'(href=["\'])((?:\.\./)*)(' + alt + r")/index\.html")
    repl = rf"\1\2{SUBDIR}/\3/index.html"
    changed = 0
    for f in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        rel = os.path.relpath(f, ROOT)
        if rel.startswith("_build" + os.sep) or rel.startswith(SUBDIR + os.sep):
            continue
        txt = open(f, encoding="utf-8", errors="replace").read()
        new, n = rx.subn(repl, txt)
        if n:
            open(f, "w", encoding="utf-8").write(new)
            changed += 1
    print(f"inserted '{SUBDIR}/' into agent links across {changed} non-agent pages")


def main():
    deepen_template()
    generate_agents.main()  # writes agents/<slug>/index.html

    # Delete the old root-level <slug>/ directories.
    removed = 0
    for s in SLUGS:
        d = os.path.join(ROOT, s)
        if os.path.isdir(d):
            shutil.rmtree(d)
            removed += 1
    print(f"removed {removed} old root-level agent directories")

    insert_agents_in_links()


if __name__ == "__main__":
    sys.exit(main())
