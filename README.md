# Alex Carmichael — Portfolio

Personal portfolio site, authored as a Claude Design canvas and deployed to GitHub Pages.

## How it works

| File | Role |
| --- | --- |
| `Alex Carmichael Portfolio.dc.html` | **Source of truth.** The canvas document — keep editing this in Claude Design. |
| `support.js` | The Claude Design runtime that renders the document in a browser. Generated; don't hand-edit. |
| `build.py` | Copies the source to `dist/index.html`, injects `<head>` metadata (title, description, social cards, `og:image`, favicon, `lang`) and a `<noscript>` fallback, then prerenders the page with headless Chrome so crawlers and no-JS clients get real content rather than the runtime's `{{ }}` template. |
| `public/` | Static files copied verbatim to the site root — currently the CV `.pdf` (linked from the three "Download CV" buttons) and `media/`. The source `.docx` lives in `cv-source/` and is deliberately **not** published. |
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

## Notes

- The page is prerendered at build time, so it has real content without JavaScript. `support.js` then pulls React and Babel from unpkg, mounts the design and drops the static copy — interactivity (accordions, the problem picker, the mobile menu) needs JS and a connection to unpkg.
- `uploads/` holds canvas image assets. Nothing in the current design references them, but they're copied to `dist/` so the paths keep working if the design starts using them.
