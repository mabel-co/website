# assurer.ai Website

Static site for [assurer.ai](https://www.assurer.ai) — "Real-time AI assurance
for financial services." An Astro static build, served from **GitHub Pages** on
the custom domain `www.assurer.ai`.

Working in this repo? Read [AGENTS.md](AGENTS.md) for layout, conventions and
deployment rules.

## Origin

Migrated as-is from the `apps/website/` directory of the private development
repository. That repository keeps the archive and Git history; this repo starts
fresh.

## Commands

```sh
make install   # npm install (first time only)
make check     # Astro type/content check + class-coverage gate — must pass before push
make style     # regenerate public/style.css (Tailwind v4, build-time)
make build     # production build to dist/
make preview   # build, then serve the production output locally
make clean     # remove dist/, node_modules/, .astro/
```

## Deployment

Merge to `main` builds and publishes via GitHub Pages
(`.github/workflows/deploy-pages.yml`). The custom domain is pinned by
`public/CNAME`; `astro.config.mjs` keeps `site: 'https://www.assurer.ai'` so
canonical and Open Graph URLs are unchanged.

Until DNS flips (Owner-side), the Pages build is previewable at the
`github.io` deployment URL from the workflow's `deploy` job.
