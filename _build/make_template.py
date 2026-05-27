#!/usr/bin/env python3
"""Derive _build/agent_template.html from a canonical agent page (alex-okpisz).

We split the page into [head+header chrome] / [agent content] / [footer chrome]
and insert {{TOKENS}} only at the spots that vary per agent. Every substitution
asserts its expected count so a markup change in the canonical page fails loudly
instead of silently producing a broken template.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON = os.path.join(ROOT, "alex-okpisz", "index.html")
OUT = os.path.join(ROOT, "_build", "agent_template.html")

CONTENT_START = '<div data-elementor-type="wp-page" data-elementor-id="1277"'
CONTENT_END = '<div class="ekit-template-content-markup ekit-template-content-footer'


def sub(pattern, repl, text, count_expected, flags=re.DOTALL, label=""):
    new, n = re.subn(pattern, repl, text, flags=flags)
    if n != count_expected:
        raise SystemExit(f"[make_template] {label!r}: expected {count_expected} replacement(s), made {n}")
    return new


def main():
    html = open(CANON, encoding="utf-8", errors="replace").read()

    i = html.index(CONTENT_START)
    j = html.index(CONTENT_END)
    head, content, foot = html[:i], html[i:j], html[j:]

    # ---- head / header chrome (everything above the agent content) ----
    head = head.replace(
        "<title>Alex Okpisz &#8211; Horizon Realty</title>",
        "<title>{{NAME}} &#8211; Horizon Realty</title>",
    )
    # oEmbed URLs carry the slug (URL-encoded). Only the lowercase slug appears here.
    head = sub(r"alex-okpisz", "{{SLUG}}", head, 2, label="oembed slug")
    # Self-referencing ?p=ID links (canonical, shortlink, skip-link, menu toggle)
    # -> point at the page's own pretty URL.
    head = head.replace("../index.html%3Fp=1277.html", "index.html")

    if "{{NAME}}" not in head:
        raise SystemExit("[make_template] title token not inserted")

    # ---- agent content block ----
    content = sub(
        r'<img\b[^>]*src="\.\./wp-content/uploads/2023/06/Alex-Okpisz-Transparent\.png"[^>]*/>',
        "{{PHOTO_IMG}}", content, 1, label="photo img",
    )
    content = sub(
        r'(<h2 class="elementor-heading-title elementor-size-default">)Alex Okpisz(</h2>)',
        r"\1{{NAME}}\2", content, 1, label="name h2",
    )
    content = sub(
        r'(<h4 class="elementor-heading-title elementor-size-default">)Sales Associate(</h4>)',
        r"\1{{TITLE}}\2", content, 1, label="role h4",
    )
    # The "Contact" icon-list item (with the obfuscated email link).
    content = sub(
        r'<li class="elementor-icon-list-item">\s*<a href="[^"]*email-protection#[0-9a-f]+">.*?icon-envelope2.*?Contact.*?</a>\s*</li>',
        "{{CONTACT_ITEM}}", content, 1, label="contact item",
    )
    # Bio: inner HTML of the text-editor widget container.
    content = sub(
        r'(widget_type="text-editor\.default">\s*<div class="elementor-widget-container">\s*).*?(\s*</div>\s*</div>)',
        r"\1{{BIO_HTML}}\2", content, 1, label="bio",
    )

    template = head + content + foot
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(template)

    tokens = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", template)))
    print(f"Wrote {OUT}")
    print("Tokens present:", ", ".join(tokens))
    print(f"Template size: {len(template)} bytes")


if __name__ == "__main__":
    sys.exit(main())
