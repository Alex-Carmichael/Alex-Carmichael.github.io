# Alex Carmichael — Portfolio

Personal portfolio site, authored as a Claude Design canvas and deployed to GitHub Pages.

## How it works

| File | Role |
| --- | --- |
| `Alex Carmichael Portfolio.dc.html` | **Source of truth.** The canvas document — keep editing this in Claude Design. |
| `support.js` | The Claude Design runtime that renders the document in a browser. Generated; don't hand-edit. |
| `build.py` | Copies the source to `dist/index.html`, injects `<head>` metadata (title, description, social cards, `og:image`, favicon, `lang`) and a `<noscript>` fallback, then prerenders the page with headless Chrome so crawlers and no-JS clients get real content rather than the runtime's `{{ }}` template. |
| `public/` | Static files copied verbatim to the site root — currently the CV `.pdf` (linked from the three "Download CV" buttons) and `media/`. The source `.docx` lives in `cv-source/` and is deliberately **not** published. |
| `tools/make_og_card.py` | Renders `public/media/og-card.png`, the social preview. Carries no client content by design. |
| `tools/redact-screenshot.html` | Regenerates the case study screenshot with the client wordmark and campaign copy blanked out. |
| `tools/cv_to_pdf.py` | Regenerates `public/Alex-Carmichael-CV.pdf` from the `.docx`. Run it after updating the CV. |
| `.github/workflows/deploy-pages.yml` | Builds and publishes `dist/` to GitHub Pages on every push to `main`. |

`dist/` is generated and git-ignored — nothing built is committed.

## Deploying

1. Create a GitHub repo and push this directory to `main`.
2. In the repo: **Settings → Pages → Build and deployment → Source = GitHub Actions**.
3. Push. The workflow builds and deploys; the live URL appears in the Actions run summary and under Settings → Pages.

Default URL is `https://<user>.github.io/<repo>/`. For a user site, name the repo `<user>.github.io` and it serves from the root.

### Custom domain

Add a `CNAME` file at the repo root containing just the domain (e.g. `alexcarmichael.dev`). The build copies it into `dist/` automatically.

## Local preview

```bash
python3 build.py && python3 -m http.server 8000 --directory dist
```

Then open <http://localhost:8000>.

## Client confidentiality

Case study 01 describes a live commercial system. The screenshot has the client's wordmark and
campaign headline blanked out (solid fills, not blur), the case study no longer names the client,
and `og:image` is a plain title card rather than the storefront. `public/media/case-01-catalogue.svg`
is an abstract diagram kept as a drop-in replacement if the screenshot needs to come out entirely.

Two things this does **not** cover: the site still describes the architecture in detail, and the
published CV names the client in its summary and first bullet.

## Notes

- The page is prerendered at build time, so it has real content without JavaScript. `support.js` then pulls React and Babel from unpkg, mounts the design and drops the static copy — interactivity (accordions, the problem picker, the mobile menu) needs JS and a connection to unpkg.
- `uploads/` holds canvas image assets. Nothing in the current design references them, but they're copied to `dist/` so the paths keep working if the design starts using them.
