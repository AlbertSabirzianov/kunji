# Website source

Pages for https://testwithsuraj.github.io/kunji/ (the docs live in `docs-site/`).

- `pages/<page>.<lang>.html` — the body of each page (`en` and `hi`).
- `scripts/build_site.py` wraps each body in the shared header, footer, theme script and SEO
  tags and writes `site/` (English) and `site/hi/` (Hindi), plus `site/sitemap.xml`.
- Shared styles and behaviour: `site/style.css` and `site/app.js` (terminal demos, theme
  toggle, mobile menu, live GitHub stars and version).

After editing, run `python scripts/build_site.py` and commit `site/` too. The Pages workflow
also runs it on every deploy.

To add a Hindi version of another page, create `pages/<page>.hi.html`; the language switch
and `hreflang` tags pick it up automatically.
