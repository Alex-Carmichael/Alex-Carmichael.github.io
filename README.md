# Alex Carmichael — Portfolio

Personal portfolio site, authored as a Claude Design canvas and deployed to GitHub Pages.

## How it works

| File | Role |
| --- | --- |
| `Alex Carmichael Portfolio.dc.html` | **Source of truth.** The canvas document — keep editing this in Claude Design. |
| `support.js` | The Claude Design runtime that renders the document in a browser. Generated; don't hand-edit. |
| `build.py` | Copies the source to `dist/index.html` and injects `<head>` metadata (title, description, social cards, favicon, `lang`) plus a `<noscript>` fallback. |
| `public/` | Static files copied verbatim to the site root — currently the CV as `.pdf` (linked from the three "Download CV" buttons) and the `.docx` it came from. |
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

- The page renders client-side: `support.js` pulls React and Babel from unpkg at load, then mounts the design. It needs JavaScript and a network connection to unpkg on first paint.
- `uploads/` holds canvas image assets. Nothing in the current design references them, but they're copied to `dist/` so the paths keep working if the design starts using them.
