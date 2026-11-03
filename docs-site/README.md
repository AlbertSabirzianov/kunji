# kunji docs

Source for https://testwithsuraj.github.io/kunji/docs/, built with
[Starlight](https://starlight.astro.build/) (Astro).

## Run locally

```bash
# from the repository root
python -m pip install -e .
python scripts/gen_docs.py        # generate reference, provider and changelog pages
cd docs-site
npm ci
npm run dev                       # http://localhost:4321/kunji/docs/
```

## Where things are

| Path | What |
| --- | --- |
| `src/content/docs/` | Pages (Markdown / MDX). Edit these. |
| `src/content/docs/reference/cli/`, `providers/*.md` (except `index.md`), `reference/chat-commands.md`, `reference/environment-variables.md`, `releases/changelog.md` | **Generated** by `scripts/gen_docs.py`; git-ignored. Change the code or the script, not these files. |
| `src/styles/kunji.css` | Theme (colours and fonts match the landing page) |
| `astro.config.mjs` | Sidebar, SEO, plugins |

## Writing guidelines

- One task per page, written for people new to the terminal; short sentences, real commands.
- Link with full paths: `/kunji/docs/guides/saved-prompts/` (the build checks every link).
- Every page needs a `description` in its frontmatter (used by search engines).
- Don't invent model names; prefer ones used elsewhere in the docs or `<model>`.

Deployed by `.github/workflows/pages.yml` together with the landing page in `site/`.
