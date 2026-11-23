# Repo-level targets for the public Assurer website (Astro).
# Run from the repository root.

.PHONY: install check style style-check build preview clean

install:
	npm install

# Astro type/content check + class-coverage gate — must pass before push;
# the deploy workflow runs `check` and `build`.
check:
	npm run check
	python3 scripts/style-class-coverage.py

style:
	npm run style:build

style-check:
	python3 scripts/style-class-coverage.py

build:
	npm run build

preview: build
	npm run preview

clean:
	rm -rf dist node_modules .astro
