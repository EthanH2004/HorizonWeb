# Agent pages — data + template framework

Agent pages used to be ~99 hand-duplicated ~72 KB HTML files (plus a `?p=<id>.html`
copy of each). They are now generated from **one data file + one template**, and live
together under `agents/`:

- **`agents.json`** — the per-agent data (the only thing that varies): `slug`, `wp_id`,
  `name`, `title`, `photo` (+ `srcset`/`width`/`height`), `contact_href`, `bio_html`.
  Asset paths are stored **root-relative** (e.g. `wp-content/...`); the generator adds
  the right number of `../` for the page's depth.
- **`agent_template.html`** — the shared page (header, nav, footer, scripts, layout)
  with `{{TOKENS}}` for the variable parts. All agents share one set of Elementor
  element IDs, so a single stylesheet (`wp-content/uploads/elementor/css/post-1277.css`)
  styles every page.
- Each **`agents/<slug>/index.html`** is **generated output** — don't hand-edit it; edit
  the data or template and regenerate.

## Edit an agent / add an agent

1. Edit `agents.json` (or add a record — `slug` becomes the URL `/agents/<slug>/`).
   Keep asset paths root-relative (no leading `../`).
2. Regenerate:

   ```sh
   python3 _build/generate_agents.py
   ```

3. If you added an agent, also add a link to it on `our-agents/index.html`
   (`href="../agents/<slug>/index.html"`).

## Scripts (run from the repo root)

| Script | Purpose |
| --- | --- |
| `generate_agents.py` | **The build step.** Renders every `agents/<slug>/index.html` from `agents.json` + `agent_template.html`. Re-run after any edit. Output dir is `AGENTS_SUBDIR`; asset paths are re-prefixed for that depth. |
| `make_template.py` | Re-derives `agent_template.html` from a canonical agent page. Only needed if the shared chrome/layout changes. Asserts each token is inserted exactly once. |
| `extract_agents.py` | **One-time migration.** Scraped the original mirror into `agents.json` (stores root-relative asset paths). Not used for normal edits. |
| `cleanup_links.py` | **One-time migration.** Rewrote `?p=<id>` agent links to pretty URLs and deleted the redundant `?p=<id>.html` / root-level `<slug>.html` agent duplicates. |
| `sectionize.py` | **One-time migration.** Did the same `?p=<id>` → pretty-URL cleanup for the *section* pages (About, Areas, Sell, …) and created `newsletter/` (the one section that lacked a pretty dir). |
| `move_agents.py` | **One-time migration.** Moved agent pages from `/<slug>/` to `/agents/<slug>/`: deepened template paths, regenerated, deleted old dirs, and inserted `agents/` into agent links everywhere. |

## Notes

- **Pretty URLs only.** No `?p=<id>.html` files or links remain anywhere. Agents live
  at `/agents/<slug>/`; section pages at `/<section>/` (e.g. `/about-us/`, `/newsletter/`).
- **Relative-path depth:** agent pages sit two levels below root, so they reach assets
  via `../../wp-content/...` and reach each other via `../<slug>/...` (siblings).
- Emails stay Cloudflare-obfuscated in the data and are decoded client-side by the
  site's existing `email-decode.min.js`, exactly as before.
- The mirror is missing some plugin `*.js` files (a pre-existing wget gap on every
  page, including `newsletter/`); CSS, images, and content are intact.
