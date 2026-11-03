# ruff: noqa: E501  (HTML templates)
"""Build the website pages in site/ from site-src/ (one shared layout, English + Hindi).

    python scripts/build_site.py

site-src/pages/<page>.<lang>.html holds each page's body. This script wraps it in the shared
header, footer, theme script and SEO tags, and writes:
    site/<page>.html        English (index.html for the home page)
    site/hi/<page>.html     Hindi
Commit the generated files in site/ too: GitHub Pages serves that folder.
"""

from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site-src" / "pages"
OUT = ROOT / "site"
SITE = "https://testwithsuraj.github.io/kunji/"
REPO = "https://github.com/testwithsuraj/kunji"

PAGES = {
    # page: (file name, nav key)
    "index": ("index.html", "home"),
    "features": ("features.html", "features"),
    "privacy": ("privacy.html", "privacy"),
    "terms": ("terms.html", "terms"),
    "404": ("404.html", "404"),
}

META = {
    ("index", "en"): ("kunji — your keys, every AI model, one terminal",
                      "kunji is a free, open-source terminal app for chatting with any AI model "
                      "using your own API keys. Live cost meter, daily budgets, compare mode, "
                      "saved prompts, chat history."),
    ("index", "hi"): ("kunji — अपनी API key से हर AI मॉडल, एक टर्मिनल में",
                      "kunji एक मुफ़्त, ओपन-सोर्स टर्मिनल ऐप है जिससे आप अपनी API key से OpenAI, "
                      "Anthropic, Gemini, Groq और Ollama जैसे किसी भी AI मॉडल से चैट कर सकते हैं।"),
    ("features", "en"): ("Features — kunji",
                         "Everything kunji does: every AI provider, switching models mid-chat, "
                         "cost meter and budgets, compare mode, saved prompts, chat history, "
                         "files, pipes and privacy."),
    ("features", "hi"): ("फ़ीचर्स — kunji",
                         "kunji के सभी फ़ीचर्स: हर AI प्रोवाइडर, चैट के बीच मॉडल बदलना, खर्च और बजट, "
                         "मॉडल की तुलना, सेव किए प्रॉम्प्ट, चैट हिस्ट्री और प्राइवेसी।"),
    ("privacy", "en"): ("Privacy policy — kunji",
                        "How kunji and this website handle your data: your API keys and prompts "
                        "never reach kunji servers."),
    ("terms", "en"): ("Terms of use — kunji", "Terms for using the kunji app and website."),
    ("404", "en"): ("Page not found — kunji", "This page doesn't exist."),
}

T = {
    "en": {
        "skip": "Skip to content", "features": "Features", "docs": "Docs", "menu": "Menu",
        "theme": "Switch between light and dark theme", "other": "हिन्दी", "other_lang": "hi",
        "other_name": "हिन्दी में देखें", "stars": "stars",
        "foot": "Kunji (कुंजी) means “key” in Hindi. Made in India, open source under Apache-2.0.",
        "links": [("docs/", "Documentation"), ("features.html", "Features"),
                  ("privacy.html", "Privacy"), ("terms.html", "Terms"),
                  (f"{REPO}/blob/main/LICENSE", "License"), (f"{REPO}/security/policy", "Security"),
                  (f"{REPO}/blob/main/CHANGELOG.md", "Changelog"),
                  (f"{REPO}/issues/new/choose", "Report a problem")],
    },
    "hi": {
        "skip": "सीधे सामग्री पर जाएँ", "features": "फ़ीचर्स", "docs": "डॉक्स", "menu": "मेन्यू",
        "theme": "लाइट और डार्क थीम बदलें", "other": "English", "other_lang": "en",
        "other_name": "View in English", "stars": "स्टार",
        "foot": "कुंजी यानी “key”। भारत में बना, Apache-2.0 लाइसेंस के तहत ओपन सोर्स।",
        "links": [("docs/", "डॉक्यूमेंटेशन"), ("features.html", "फ़ीचर्स"),
                  ("privacy.html", "प्राइवेसी"), ("terms.html", "शर्तें"),
                  (f"{REPO}/blob/main/LICENSE", "लाइसेंस"),
                  (f"{REPO}/issues/new/choose", "समस्या बताएँ")],
    },
}

LOGO = ('<svg viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="7" '
        'fill="#14201A"/><circle cx="11" cy="16" r="5" fill="none" stroke="#3DDC84" '
        'stroke-width="3"/><path d="M16 16h11M22 16v4M26 16v3" stroke="#3DDC84" stroke-width="3" '
        'stroke-linecap="round"/></svg>')
SUN = ('<svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
       'stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2'
       'M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4'
       '-1.4"/></svg>')
MOON = ('<svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"'
        ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 '
        '0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>')
BARS = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>')
STAR = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.3l2 4.2 4.6.6-3.4 3.2.9 4.5L8 11.6l-4.1 2.2.9-4.5L1.4 6.1 6 5.5z"/></svg>'

THEME_SCRIPT = (
    "<script>(function(){var t;try{t=localStorage.getItem('starlight-theme')}catch(e){}"
    "var d=t==='dark'||((!t||t==='auto')&&window.matchMedia&&"
    "matchMedia('(prefers-color-scheme: dark)').matches);"
    "document.documentElement.dataset.theme=d?'dark':'light'})();</script>"
)


def url(page: str, lang: str) -> str:
    file = PAGES[page][0]
    path = ("hi/" if lang == "hi" else "") + ("" if file == "index.html" else file)
    return SITE + path


def langs_for(page: str) -> list[str]:
    return [lang for lang in ("en", "hi") if (SRC / f"{page}.{lang}.html").exists()]


def layout(page: str, lang: str, body: str) -> str:
    t = T[lang]
    up = "../" if lang == "hi" else ""          # path to site root
    home = "./" if lang == "en" else "./"
    en_root = "../" if lang == "hi" else ""
    title, description = META.get((page, lang), META[(page, "en")])
    nav_key = PAGES[page][1]
    available = langs_for(page)

    other = t["other_lang"]
    if other in available:
        other_href = (("hi/" if other == "hi" else "../") + ("" if PAGES[page][0] == "index.html"
                      else PAGES[page][0]))
    else:
        other_href = "hi/" if other == "hi" else "../"
    if lang == "en" and other == "hi" and "hi" not in available:
        other_href = "hi/"

    alternates = "".join(
        f'<link rel="alternate" hreflang="{a}" href="{url(page, a)}">' for a in available
    )
    if len(available) > 1:
        alternates += f'<link rel="alternate" hreflang="x-default" href="{url(page, "en")}">'

    def nav_link(href: str, label: str, key: str) -> str:
        current = ' aria-current="page"' if key == nav_key else ""
        return f'<a href="{href}"{current}>{label}</a>'

    # Pages only English (privacy, terms, 404) link to the English versions from Hindi pages.
    def local(target: str) -> str:
        name = target.split(".")[0]
        if lang == "hi" and name in ("privacy", "terms") and "hi" not in langs_for(name):
            return en_root + target
        return target

    foot_links = "".join(
        f'<li><a href="{href if href.startswith("http") else (up + href if href.startswith("docs/") else local(href))}">{label}</a></li>'
        for href, label in t["links"]
    )
    robots = '<meta name="robots" content="noindex">' if page == "404" else ""
    base_path = "/kunji/" if page == "404" else up
    canonical = "" if page == "404" else f'<link rel="canonical" href="{url(page, lang)}">'
    og_locale = "hi_IN" if lang == "hi" else "en_US"

    return f"""<!doctype html>
<html lang="{lang}" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
{canonical}{alternates}{robots}
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="{og_locale}">
<meta property="og:url" content="{url(page, lang)}">
<meta property="og:image" content="{SITE}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE}og.png">
<meta name="theme-color" content="#ECEFEC" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#101814" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{base_path}favicon.svg" type="image/svg+xml">
{THEME_SCRIPT}
<link rel="stylesheet" href="{base_path}style.css">
</head>
<body>
<a class="skip" href="#main">{t["skip"]}</a>
<header class="site-header">
  <div class="wrap bar">
    <a class="brand" href="{base_path if page == '404' else home}" aria-label="kunji home">{LOGO}kunji</a>
    <button class="icon-btn menu-btn" type="button" aria-expanded="false" aria-controls="nav" aria-label="{t["menu"]}">{BARS}</button>
    <nav id="nav" class="nav" aria-label="Main">
      {nav_link((base_path if page == '404' else '') + 'features.html', t["features"], "features")}
      {nav_link(('/kunji/' if page == '404' else up) + 'docs/', t["docs"], "docs")}
      <a href="{REPO}" class="gh">GitHub<span class="stars" data-stars hidden>{STAR}<span data-stars-count></span><span class="sr-only"> {t["stars"]}</span></span></a>
      <span class="tools">
        <a class="lang" href="{('/kunji/hi/' if page == '404' else other_href)}" hreflang="{other}" lang="{other}" title="{t["other_name"]}">{t["other"]}</a>
        <button class="icon-btn theme-btn" type="button" aria-label="{t["theme"]}" title="{t["theme"]}">{SUN}{MOON}</button>
      </span>
    </nav>
  </div>
</header>

<main id="main">
{body}
</main>

<footer>
  <div class="wrap">
    <p>{t["foot"]}</p>
    <ul class="foot-links">{foot_links}</ul>
  </div>
</footer>
<script src="{base_path}app.js" defer></script>
</body>
</html>
"""


def main() -> int:
    written = []
    for page, (file, _) in PAGES.items():
        for lang in langs_for(page):
            body = (SRC / f"{page}.{lang}.html").read_text(encoding="utf-8").strip()
            out = OUT / ("hi" if lang == "hi" else "") / file
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(layout(page, lang, body), encoding="utf-8")
            written.append(str(out.relative_to(ROOT)))
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
               'xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for page in PAGES:
        if page == "404":
            continue
        available = langs_for(page)
        for lang in available:
            alts = "".join(f'<xhtml:link rel="alternate" hreflang="{a}" href="{url(page, a)}"/>'
                           for a in available) if len(available) > 1 else ""
            sitemap.append(f"  <url><loc>{url(page, lang)}</loc>{alts}</url>")
    sitemap.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")
    print("wrote", ", ".join(written), "and site/sitemap.xml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
