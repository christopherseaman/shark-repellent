# shark.badmath.org Cloudflare Worker

Serves the shark-repellent install script and proxies file paths to GitHub raw.

## Routes

- `GET /` → returns the contents of the repo's `install.sh` as `text/x-shellscript`. Lets `curl -fsSL shark.badmath.org | bash` work without specifying a path.
- `GET /<path>` → 302 redirects to `https://raw.githubusercontent.com/christopherseaman/shark-repellent/main/<path>`.

## Deploy

```bash
npm install -g wrangler   # one-time
wrangler login            # browser-based auth
wrangler deploy
```

DNS: in the Cloudflare dashboard for `badmath.org`, add a CNAME record `shark` → `<your-account>.workers.dev` (or use the Workers Routes UI). The `routes` block in `wrangler.toml` handles the runtime binding once DNS resolves.

## Local testing

```bash
wrangler dev                          # serves on http://localhost:8787
curl http://localhost:8787            # should return install.sh body
curl -I http://localhost:8787/datasci/ttest.py   # should be 302 to raw.githubusercontent.com
```
