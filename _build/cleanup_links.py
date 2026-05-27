#!/usr/bin/env python3
"""Convert agent ?p=<id> links to pretty /<slug>/ URLs and delete the redundant
index.html?p=<id>.html agent duplicates.

Order matters: the shared template carries the site nav/footer (which links to every
agent), so we rewrite the template first, regenerate, then sweep the remaining static
pages. Both `index.html?p=ID.html` and `<slug>/index.html` are root-relative, so any
`../` prefix already on a link is preserved automatically.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "_build")
sys.path.insert(0, BUILD)
import generate_agents  # noqa: E402
from extract_agents import ROOT_FILE_AGENTS  # noqa: E402

agents = json.load(open(os.path.join(BUILD, "agents.json"), encoding="utf-8"))
ID2SLUG = {a["wp_id"]: a["slug"] for a in agents if a.get("wp_id")}
DUP_FILES = {f"index.html?p={i}.html" for i in ID2SLUG}
# Root-level <slug>.html agent files (e.g. mindy-walker.html) -> <slug>/index.html.
ROOTFILE2SLUG = {fn: slug for slug, fn in ROOT_FILE_AGENTS.items()}

# Match `index.html%3Fp=<id>.html` only for known agent ids.
RX = re.compile(
    r"index\.html%3Fp=(" + "|".join(re.escape(i) for i in ID2SLUG) + r")\.html"
)


def rewrite_file(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    new, n = RX.subn(lambda m: f"{ID2SLUG[m.group(1)]}/index.html", txt)
    for fn, slug in ROOTFILE2SLUG.items():
        new, k = re.subn(re.escape(fn), f"{slug}/index.html", new)
        n += k
    if n:
        open(path, "w", encoding="utf-8").write(new)
    return n


def main():
    # 1) Template (carries the nav/footer agent links).
    tpl = os.path.join(BUILD, "agent_template.html")
    print(f"template: rewrote {rewrite_file(tpl)} agent links")

    # 2) Regenerate so every agent page picks up the clean nav.
    generate_agents.main()

    # 3) Sweep all remaining static .html (agent pages now contribute 0).
    total, files = 0, 0
    for f in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        rel = os.path.relpath(f, ROOT)
        if rel.startswith("_build" + os.sep) or os.path.basename(rel) in DUP_FILES or rel in DUP_FILES:
            continue
        n = rewrite_file(f)
        if n:
            total += n
            files += 1
    print(f"static sweep: rewrote {total} agent links across {files} files")

    # 4) Delete the redundant duplicates: ?p=<id>.html and root-level <slug>.html.
    deleted = 0
    for fn in list(DUP_FILES) + list(ROOTFILE2SLUG):
        p = os.path.join(ROOT, fn)
        if os.path.exists(p):
            os.remove(p)
            deleted += 1
    print(f"deleted {deleted} redundant duplicate files")


if __name__ == "__main__":
    sys.exit(main())
