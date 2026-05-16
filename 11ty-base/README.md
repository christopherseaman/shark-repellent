# 11ty baseline

A minimal shared Eleventy 3.x scaffold. After installing into a project root:

1. `npm install`
2. Edit `_data/nav.js` — set `project` and populate `sections`.
3. Add markdown files at the project root or in subdirs. They render through `_includes/base.njk`.
4. `npm start` for local dev; `npm run build` to produce `_site/`.

## Customization points

- **Navigation** — `_data/nav.js`. Each entry in `sections` is `{title, items: [{url, label}]}`.
- **Styles** — `css/main.css` and `css/prism-dark.css`. Replace wholesale to restyle.
- **Layout** — `_includes/base.njk` (page chrome) and `_includes/sidebar.njk` (nav rendering).
- **Eleventy config** — add per-project transforms, passthroughs, computed-data blocks in `.eleventy.js`. The baseline only ships markdownIt + plugins + the `css/` passthrough.

## GitHub Pages

The `build:ghpages` script in `package.json` includes a `<PATHPREFIX>` token. Replace with your repo name (e.g., `npx @11ty/eleventy --pathprefix=/my-site`) so links resolve correctly under `https://<user>.github.io/<repo>/`.
