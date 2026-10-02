#!/usr/bin/env python3
"""Render the CIPHERA legal markdown into HTML templates under drafts/.

    python3 tools/build-legal.py [path/to/Ciphera/docs/legal]

Reads privacy-policy.md, privacy-policy.ro.md, terms-of-use.md and terms-of-use.ro.md (the source of truth, in the
CIPHERA repository; this script only reads them) and writes drafts/privacy.html.in, drafts/privacy-ro.html.in,
drafts/terms.html.in and drafts/terms-ro.html.in in the site's style. Every {{FIELD}} of the markdown is kept verbatim,
so the result is a template, not a page: tools/fill-and-publish.sh fills the fields and moves the pages to the root.
The .in suffix means GitHub Pages never serves them as web pages.
"""
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_SRC = pathlib.Path(
    "/Users/stefanepistatu/Library/Mobile Documents/com~apple~CloudDocs/Aplicatii IOS Create /Ciphera/docs/legal"
)

FIELD = re.compile(r"\{\{[A-Z0-9_]+\}\}")

NAV = {
    "en": [("./", "Home", "home"), ("support.html", "Support", "support"),
           ("privacy.html", "Privacy Policy", "privacy"), ("terms.html", "Terms of Service", "terms")],
    "ro": [("./", "Acasă", "home"), ("support.html", "Asistență", "support"),
           ("privacy-ro.html", "Confidențialitate", "privacy"), ("terms-ro.html", "Termenii serviciului", "terms")],
}
TAGLINE = {
    "en": "End-to-end encrypted messages, calls and files · iPhone, iPad and Mac",
    "ro": "Mesaje, apeluri și fișiere criptate end-to-end · iPhone, iPad și Mac",
}
FOOTER_NOTE = {
    "en": "Static site: no cookies, no scripts, no tracking.",
    "ro": "Site static: fără cookie-uri, fără scripturi, fără urmărire.",
}

# (markdown file, output template, lang, nav key, <title>, meta description, twin page, twin label)
PAGES = [
    ("privacy-policy.md", "privacy.html.in", "en", "privacy", "Privacy Policy · CIPHERA Encrypted Chat",
     "What personal data the CIPHERA service processes, why, for how long, and your rights under the GDPR.",
     "privacy-ro.html", "Versiunea în limba română"),
    ("privacy-policy.ro.md", "privacy-ro.html.in", "ro", "privacy", "Politica de confidențialitate · CIPHERA Encrypted Chat",
     "Ce date personale prelucrează serviciul CIPHERA, de ce, cât timp și ce drepturi ai conform GDPR.",
     "privacy.html", "English version"),
    ("terms-of-use.md", "terms.html.in", "en", "terms", "Terms of Service · CIPHERA Encrypted Chat",
     "The terms of the CIPHERA messaging service: who may use it, the subscription and free use through your organization, acceptable use, reporting and enforcement.",
     "terms-ro.html", "Versiunea în limba română"),
    ("terms-of-use.ro.md", "terms-ro.html.in", "ro", "terms", "Termenii serviciului · CIPHERA Encrypted Chat",
     "Termenii serviciului de mesagerie CIPHERA: cine îl poate folosi, abonamentul și folosirea gratuită prin organizație, folosire acceptabilă, raportare și măsuri.",
     "terms.html", "English version"),
]


def inline(text: str) -> str:
    """Escape HTML, then apply the little markdown these files use: **bold** and bare URLs."""
    out = html.escape(text, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\"'>])(https?://[^\s<)]+)", r'<a href="\1">\1</a>', out)
    return out


def render_body(md: str, twin: str, twin_label: str) -> str:
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)  # the publication-gate comment is not part of the page
    lines = md.splitlines()
    out, para, items, rows = [], [], [], []

    def flush():
        nonlocal para, items, rows
        if para:
            out.append("<p>" + inline(" ".join(s.strip() for s in para)) + "</p>")
            para = []
        if items:
            out.append("<ul>\n" + "\n".join("  <li>" + inline(i) + "</li>" for i in items) + "\n</ul>")
            items = []
        if rows:
            head, body = rows[0], rows[1:]
            t = ["<table>", "  <tr>" + "".join("<th>" + inline(c) + "</th>" for c in head) + "</tr>"]
            for r in body:
                t.append("  <tr>" + "".join("<td>" + inline(c) + "</td>" for c in r) + "</tr>")
            t.append("</table>")
            out.append("\n".join(t))
            rows = []

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        if line.startswith("# "):
            flush()
            out.append("<h2>" + inline(line[2:].strip()) + "</h2>")
            continue
        if line.startswith("## "):
            flush()
            text = line[3:].strip()
            m = re.match(r"(\d+)\.", text)
            anchor = f' id="s{m.group(1)}"' if m else ""
            out.append(f"<h3{anchor}>" + inline(text) + "</h3>")
            continue
        if re.match(r"^(Effective date|Data intrării în vigoare):", line):
            flush()
            out.append('<p class="meta">' + inline(line.strip()) + f' · <a href="{twin}">{twin_label}</a></p>')
            continue
        if line.lstrip().startswith("|"):
            if para or items:
                flush()
            if re.match(r"^\|?\s*:?-{3,}", line.strip()):
                continue  # header separator
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cells)
            continue
        if rows:
            flush()
        if line.startswith("- "):
            if para:
                flush()
            items.append(line[2:].strip())
            continue
        if items and line.startswith("  "):
            items[-1] += " " + line.strip()
            continue
        if items:
            flush()
        para.append(line)
    flush()
    return "\n\n".join(out)


def page(lang: str, nav_key: str, title: str, description: str, body: str, twin: str, twin_label: str) -> str:
    links = []
    for href, label, key in NAV[lang]:
        cls = ' class="on"' if key == nav_key else ""
        links.append(f'      <a href="{href}"{cls}>{label}</a>')
    links.append(f'      <a href="{twin}">{"Română" if lang == "en" else "English"}</a>')
    nav = "\n".join(links)
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta name="theme-color" content="#050B18">
<link rel="icon" type="image/png" sizes="256x256" href="icon-256.png">
<link rel="apple-touch-icon" href="icon-256.png">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
  <div class="wrap">
    <div class="brand">
      <img class="mark" src="icon-256.png" width="44" height="44" alt="">
      <div>
        <h1>CIPHERA Encrypted Chat</h1>
        <p>{TAGLINE[lang]}</p>
      </div>
    </div>
    <nav>
{nav}
    </nav>
  </div>
</header>
<main><div class="wrap">
{body}

</div></main>
<footer><div class="wrap">
  © 2026 MSCS di Stefan E. · CIPHERA Encrypted Chat · <a href="mailto:stefan@support-remote.org">stefan@support-remote.org</a><br>
  {FOOTER_NOTE[lang]}
</div></footer>
</body>
</html>
"""


def main() -> int:
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    if not src.is_dir():
        print(f"not a directory: {src}", file=sys.stderr)
        return 2
    drafts = ROOT / "drafts"
    drafts.mkdir(exist_ok=True)
    fields = {}
    for md_name, out_name, lang, nav_key, title, desc, twin, twin_label in PAGES:
        md = (src / md_name).read_text(encoding="utf-8")
        body = render_body(md, twin, twin_label)
        doc = page(lang, nav_key, title, desc, body, twin, twin_label)
        (drafts / out_name).write_text(doc, encoding="utf-8")
        fields[out_name] = sorted(set(FIELD.findall(body)))
        print(f"wrote drafts/{out_name}: fields {', '.join(fields[out_name]) or 'none'}")
    status = 0
    for en, ro in (("privacy.html.in", "privacy-ro.html.in"), ("terms.html.in", "terms-ro.html.in")):
        if fields[en] != fields[ro]:
            print(f"FAIL {en} and {ro} use different fields: {fields[en]} vs {fields[ro]}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
