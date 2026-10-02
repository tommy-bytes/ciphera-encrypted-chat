#!/usr/bin/env bash
# Fills the {{FIELD}}s of the legal templates in drafts/, writes privacy.html, privacy-ro.html, terms.html and
# terms-ro.html to the site root, verifies them, commits and pushes — so GitHub Pages publishes them.
#
#   CONTROLLER_ADDRESS="Via …, 00100 Roma, Italia" \
#   CONTROLLER_COUNTRY="Italy" \
#   EFFECTIVE_DATE="15 October 2026" \
#   PRIVACY_EMAIL="privacy@example.org" \
#   SUPPORT_EMAIL="stefan@support-remote.org" \
#   bash tools/fill-and-publish.sh
#
# Required: CONTROLLER_ADDRESS, CONTROLLER_COUNTRY, EFFECTIVE_DATE, PRIVACY_EMAIL, SUPPORT_EMAIL.
# Known defaults (override if needed): HOSTING_REGION="Italy North (Milan)", HOSTING_REGION_RO="Italy North (Milano)".
# Optional Romanian wording, default = the English value: EFFECTIVE_DATE_RO ("15 octombrie 2026"),
# CONTROLLER_COUNTRY_RO (genitive, e.g. "Italiei" — the text reads "legea {{CONTROLLER_COUNTRY}}").
# NO_PUSH=1 fills and verifies only (nothing is committed).
#
# Run it from a clone of tommy-bytes/ciphera-encrypted-chat (not from the CIPHERA repository).
# When the markdown in Ciphera/docs/legal changes, run `python3 tools/build-legal.py` first to refresh drafts/.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

origin="$(git remote get-url origin 2>/dev/null || true)"
case "$origin" in
  *ciphera-encrypted-chat*) ;;
  *) echo "Refusing: origin is '$origin', not the ciphera-encrypted-chat pages repository." >&2; exit 2 ;;
esac

: "${HOSTING_REGION:=Italy North (Milan)}"
: "${HOSTING_REGION_RO:=Italy North (Milano)}"
missing=()
for v in CONTROLLER_ADDRESS CONTROLLER_COUNTRY EFFECTIVE_DATE PRIVACY_EMAIL SUPPORT_EMAIL; do
  [ -n "${!v:-}" ] || missing+=("$v")
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "Missing values: ${missing[*]}" >&2
  echo "Set them as environment variables (see the header of this script)." >&2
  exit 2
fi
: "${EFFECTIVE_DATE_RO:=$EFFECTIVE_DATE}"
: "${CONTROLLER_COUNTRY_RO:=$CONTROLLER_COUNTRY}"
export CONTROLLER_ADDRESS CONTROLLER_COUNTRY CONTROLLER_COUNTRY_RO EFFECTIVE_DATE EFFECTIVE_DATE_RO \
       PRIVACY_EMAIL SUPPORT_EMAIL HOSTING_REGION HOSTING_REGION_RO

python3 - <<'PY'
import html, os, pathlib, re, sys
root = pathlib.Path(".")
B6 = re.compile(r"this build|placeholder|not configured|roadmap|phase [0-9]|faza [0-9]|coming soon|not built yet|"
                r"\bTODO\b|de completat|to be completed|lorem ipsum", re.I)
FIELD = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
pages = {"privacy.html": "en", "privacy-ro.html": "ro", "terms.html": "en", "terms-ro.html": "ro"}

def value(name, lang):
    v = os.environ.get(f"{name}_RO") if lang == "ro" else None
    v = v or os.environ.get(name)
    if not v:
        sys.exit(f"no value for {name}")
    esc = html.escape(v, quote=False)
    if name.endswith("_EMAIL"):
        return f'<a href="mailto:{esc}">{esc}</a>'
    return esc

failed = False
for out_name, lang in pages.items():
    tmpl = root / "drafts" / (out_name + ".in")
    text = tmpl.read_text(encoding="utf-8")
    text = FIELD.sub(lambda m: value(m.group(1), lang), text)
    left = sorted(set(FIELD.findall(text)))
    if left:
        print(f"FAIL {out_name}: still unfilled: {left}"); failed = True
    body = text.split("<main>", 1)[-1]
    for n, line in enumerate(body.splitlines(), 1):
        if B6.search(line):
            print(f"FAIL {out_name}: forbidden phrase (rule B6): {line.strip()[:120]}"); failed = True
    if not failed:
        (root / out_name).write_text(text, encoding="utf-8")
        print(f"wrote {out_name}")
sys.exit(1 if failed else 0)
PY

if [ "${NO_PUSH:-}" = "1" ]; then
  echo "NO_PUSH=1: pages written to the root but not committed."
  exit 0
fi

git add privacy.html privacy-ro.html terms.html terms-ro.html
if git diff --cached --quiet; then echo "Nothing changed."; exit 0; fi
git -c user.name="${GIT_AUTHOR_NAME:-$(git config user.name)}" commit -q -m "Publish privacy policy and terms (effective ${EFFECTIVE_DATE})"
git -c credential.helper='!gh auth git-credential' push origin main
echo "Pushed. GitHub Pages usually rebuilds within a few minutes."

base="https://tommy-bytes.github.io/ciphera-encrypted-chat"
for i in $(seq 1 40); do
  ok=1
  for p in privacy.html privacy-ro.html terms.html terms-ro.html; do
    # Cache-buster: GitHub Pages' CDN keeps the earlier 404 for up to 10 minutes.
    code="$(curl -s -o /dev/null -L --max-time 15 -w '%{http_code}' "$base/$p?cb=$(date +%s)$RANDOM" || true)"
    [ "$code" = "200" ] || ok=0
  done
  if [ "$ok" = 1 ]; then
    for p in privacy.html privacy-ro.html terms.html terms-ro.html; do echo "OK 200 $base/$p"; done
    echo "Next, in the CIPHERA repository: bash docs/legal/check-publishable.sh --live (every page the apps link, live content)."
    exit 0
  fi
  sleep 15
done
echo "Pages not yet live after 10 minutes; check later with: curl -sI $base/privacy.html" >&2
exit 1
