#!/usr/bin/env python3
"""Render every /<slug>/index.html from agents.json + agent_template.html.

This is the build step: agents.json + agent_template.html are the single source of
truth; the per-agent HTML files are disposable output. Re-run after editing either.
"""
import html as htmllib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "_build")
# Agent pages live under this subdirectory: /agents/<slug>/index.html
AGENTS_SUBDIR = "agents"

# Asset paths in agents.json are stored root-relative (e.g. "wp-content/..."); the
# rendered page sits at <AGENTS_SUBDIR>/<slug>/index.html, so root-reaching links need
# this many "../" to climb back to the site root.
_DEPTH = len(AGENTS_SUBDIR.strip("/").split("/")) + 1
ASSET_PREFIX = "../" * _DEPTH
_ASSET_RX = re.compile(r"(?<![./\w])(wp-content|wp-includes|wp-json|cdn-cgi|idx|feed)/")


def rebase(s):
    """Prefix root-relative asset paths so they resolve from the agent page's depth."""
    return _ASSET_RX.sub(ASSET_PREFIX + r"\1/", s) if s else s


def esc(s):
    """Escape text for an HTML text node."""
    return htmllib.escape(s or "", quote=False)


def build_photo_img(a):
    src = rebase(a.get("photo"))
    if not src:
        return ""
    w = a.get("photo_width") or "600"
    h = a.get("photo_height") or "600"
    alt = htmllib.escape(a.get("name") or "", quote=True)
    srcset = rebase(a.get("photo_srcset"))
    parts = [
        '<img decoding="async"',
        f'width="{w}" height="{h}"',
        f'src="{src}"',
        'class="attachment-full size-full"',
        f'alt="{alt}"',
    ]
    if srcset:
        parts.append(f'srcset="{srcset}"')
        parts.append(f'sizes="(max-width: {w}px) 100vw, {w}px"')
    return " ".join(parts) + " />"


def build_contact_item(a):
    href = a.get("contact_href")
    icon = (
        '<span class="elementor-icon-list-icon">'
        '<i aria-hidden="true" class="icon icon-envelope2"></i></span>'
        '<span class="elementor-icon-list-text">Contact</span>'
    )
    if href:
        inner = f'<a href="{href}">{icon}</a>'
    else:
        inner = icon
    return f'<li class="elementor-icon-list-item">{inner}</li>'


def render(template, a):
    out = template
    out = out.replace("{{SLUG}}", a["slug"])
    out = out.replace("{{NAME}}", esc(a.get("name")))
    out = out.replace("{{TITLE}}", esc(a.get("title")))
    out = out.replace("{{PHOTO_IMG}}", build_photo_img(a))
    out = out.replace("{{CONTACT_ITEM}}", build_contact_item(a))
    # Bio is preserved verbatim, with any embedded asset paths rebased to page depth.
    out = out.replace("{{BIO_HTML}}", rebase(a.get("bio_html") or ""))
    return out


def main():
    template = open(os.path.join(BUILD, "agent_template.html"), encoding="utf-8").read()
    agents = json.load(open(os.path.join(BUILD, "agents.json"), encoding="utf-8"))

    written = 0
    for a in agents:
        page = render(template, a)
        leftover = re.findall(r"\{\{[A-Z_]+\}\}", page)
        if leftover:
            raise SystemExit(f"[generate] {a['slug']}: unresolved tokens {set(leftover)}")
        d = os.path.join(ROOT, AGENTS_SUBDIR, a["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
        written += 1

    print(f"Generated {written} agent pages from template + agents.json")


if __name__ == "__main__":
    sys.exit(main())
