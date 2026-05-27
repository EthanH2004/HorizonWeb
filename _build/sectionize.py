#!/usr/bin/env python3
"""One-time migration (Phase 1): convert the remaining WordPress ?p=<id> section
links to pretty /<dir>/ URLs and delete the redundant index.html?p=<id>.html files.

Nine sections already have pretty directories; Newsletter does not, so we materialize
newsletter/index.html from its ?p= copy (prefixing its bare root-relative paths with
../ since it moves from root to depth 1).
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "_build", "agent_template.html")

# WordPress page id -> pretty directory.
SECTIONS = {
    "1005": "sell",
    "1078": "newsletter",
    "326": "about-us",
    "503": "areas",
    "598": "contact-us",
    "6451": "our-office",
    "684": "join-our-brokerage",
    "7458": "mortgage-calculator",
    "765": "management-team",
    "840": "our-agents",
}
DUP_FILES = {f"index.html?p={i}.html" for i in SECTIONS}


_SKIP = re.compile(r"(?:[a-z][a-z0-9+.-]*:|//|/|#|\.\.?/|\{)")


def prefix_href_src(html, prefix="../"):
    """Prepend `prefix` to bare root-relative URLs in href/src and srcset attributes."""
    def pfx(url):
        return url if (not url or _SKIP.match(url)) else prefix + url

    def fix_single(m):
        attr, q, val = m.group(1), m.group(2), m.group(3)
        return f"{attr}={q}{pfx(val)}{q}"

    def fix_set(m):
        attr, q, val = m.group(1), m.group(2), m.group(3)
        out = []
        for item in (i.strip() for i in val.split(",")):
            if not item:
                continue
            bits = item.split(None, 1)
            bits[0] = pfx(bits[0])
            out.append(" ".join(bits))
        return f"{attr}={q}{', '.join(out)}{q}"

    html = re.sub(r'\b(href|src)=(["\'])([^"\']*)\2', fix_single, html)
    html = re.sub(r'\b(srcset|imagesrcset)=(["\'])([^"\']*)\2', fix_set, html)
    return html


def rewrite_sections(html):
    for i, d in SECTIONS.items():
        html = html.replace(f"index.html%3Fp={i}.html", f"{d}/index.html")
    return html


def main():
    # 1) Materialize newsletter/index.html (root-context -> depth 1).
    src = open(os.path.join(ROOT, "index.html?p=1078.html"), encoding="utf-8", errors="replace").read()
    src = prefix_href_src(src)
    os.makedirs(os.path.join(ROOT, "newsletter"), exist_ok=True)
    open(os.path.join(ROOT, "newsletter", "index.html"), "w", encoding="utf-8").write(src)
    print("created newsletter/index.html")

    # 2) Rewrite section ?p= links across the tree + the agent template.
    targets = [f for f in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)
               if "_build" + os.sep not in f and os.path.basename(f) not in DUP_FILES]
    targets.append(TEMPLATE)
    changed = 0
    for f in targets:
        txt = open(f, encoding="utf-8", errors="replace").read()
        new = rewrite_sections(txt)
        if new != txt:
            open(f, "w", encoding="utf-8").write(new)
            changed += 1
    print(f"rewrote section links in {changed} files")

    # 3) Delete the redundant ?p=<id>.html section duplicates.
    deleted = 0
    for fn in DUP_FILES:
        p = os.path.join(ROOT, fn)
        if os.path.exists(p):
            os.remove(p)
            deleted += 1
    print(f"deleted {deleted} redundant ?p=<id>.html section duplicates")


if __name__ == "__main__":
    sys.exit(main())
