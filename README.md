# CIPHERA Encrypted Chat — public site

Source of the GitHub Pages site for the **CIPHERA Encrypted Chat** app (end-to-end encrypted messaging for
iPhone, iPad and Mac, provided free of charge to IPSTSO members). Rights holder: MSCS di Stefan E.

| Page | Used in App Store Connect as |
|---|---|
| `index.html` | Marketing URL |
| `support.html` | Support URL (App Review 1.2: contact information and abuse reports) |
| `privacy.html` | Privacy Policy URL (Romanian version: `privacy-ro.html`) |
| `terms.html` | Terms of Service linked from the app and the description (Romanian version: `terms-ro.html`) |

Static site: no JavaScript, no cookies, no tracking.

## Legal pages

The privacy policy and the terms are generated from the markdown in the CIPHERA repository
(`docs/legal/*.md`) by `tools/build-legal.py` into `drafts/*.html.in`. They are **templates**: they still contain
`{{FIELD}}` values that are not final, so they are not published (the `.in` suffix keeps GitHub Pages from serving
them as web pages). To publish them:

```sh
CONTROLLER_ADDRESS="…" CONTROLLER_COUNTRY="…" EFFECTIVE_DATE="…" PRIVACY_EMAIL="…" SUPPORT_EMAIL="…" \
bash tools/fill-and-publish.sh
```

The script fills the fields, writes the four pages to the root, refuses any page that still has an unfilled field,
commits, pushes and waits for the pages to answer HTTP 200. See the header of the script for the optional values.

## What is not kept here

No member list, no e-mail addresses of members, no keys, no server configuration. The repository is public.
