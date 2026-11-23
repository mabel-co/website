# Assurer Website

> **Experimental — AI-generated, not human-validated.** This repository is
> built by an AI agent team under human ownership. Its contents have **not
> been validated by human experts**; we publish it for you to explore and give
> feedback on, not for production or compliance use. There is **no guarantee
> that anything here is correct or complete, and no liability is accepted**
> for its use. Nothing here is professional, compliance, or legal advice.
> The licence terms (including warranty disclaimers) apply in full.

Static site for the Assurer organisation — "Real-time AI assurance
for financial services." An Astro static build, served from **GitHub Pages** at
<https://mabel-co.github.io/website>.

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
No custom domain is used; `astro.config.mjs` sets
`site: 'https://mabel-co.github.io/website'` and `base: '/website'` so canonical and
Open Graph URLs resolve at the Pages path.

Pages must be enabled for the repo (Owner-side) before the deploy job
succeeds; until then builds upload the artifact but do not publish.
