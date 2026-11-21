# Orsay docs

Source of [docs.orsay.ai](https://docs.orsay.ai), built with [Mintlify](https://mintlify.com).

## Layout

```
docs.json               navigation, redirects, theme
custom.css              brand overrides (loaded on every page)
footer-whatsapp.js      WhatsApp icon in the footer (loaded on every page)
fr/ and en/             one folder per language, same tree in both
  home.mdx
  changelog.mdx
  personal-whatsapp/    setup guide, one numbered page per step
  whatsapp-api/
  instagram-inbound/
  features/             agents, voice cloning, campaigns, analytics...
  resources/            FAQ, pricing, prompts, API
images/                 screenshots, same sections as the pages
  features/
  whatsapp-api/
  zapier/               shared by personal-whatsapp and whatsapp-api
  resources/
logo/                   logo and favicon
```

A page added in `fr/` gets its twin in `en/` at the same path, and both go in `docs.json`.
Screenshots are named after what they show (`images/zapier/new-zap.png`), never by number.
When a page moves, add a redirect from the old URL in `docs.json`.

## Run locally

```bash
npx mint@latest dev
```

The site runs on http://localhost:3000.

## Check links before pushing

```bash
npx mint@latest broken-links
```
