# Syncing local markdown with Notion via `ntn`

Practical workflow for pushing local `.md` files to a single Notion root page
and keeping them updated. Assumes one root page in Notion; each tracked
markdown file becomes a sub-page directly under it.

The helper script is `notion-sync.sh` in this directory. The same operations are
available as plain `ntn` invocations if you prefer — see "Without the helper"
at the bottom.

---

## Prerequisites

```bash
# 1. Install ntn (https://developers.notion.com/cli/get-started/overview)
# 2. Log in once. On a headless box (SSH, WSL, server) the OS keychain may
#    not be writable; use file-based auth instead:
NOTION_KEYRING=0 ntn login

# 3. Verify auth:
NOTION_KEYRING=0 ntn doctor      # all checks should be green

# 4. jq is required for the helper script:
which jq || sudo apt install jq   # or brew install jq, etc.

# 5. (Optional) put the helper on your PATH:
ln -s "$(pwd)/notion-sync.sh" ~/bin/notion-sync
```

If you set `NOTION_KEYRING=0` for login, set it again in any shell that runs
sync commands — or export it once in your shell profile. The helper script
does not set it for you.

---

## One-time setup per project

Pick the Notion page that will hold all your synced files. Copy its URL or
page ID. Then in the project directory:

```bash
# Option A: export it (recommended — set once, forget)
export NOTION_SYNC_ROOT=https://www.notion.so/yourws/Reports-361d9fdd1a1a8052abf3da510deb5102

# Option B: project-local via direnv
echo 'export NOTION_SYNC_ROOT=<url-or-id>' > .envrc
direnv allow
```

The helper accepts either the full URL or just the page ID. ntn extracts the
UUID itself.

The script writes a `.notion-sync.tsv` file in the current directory that
maps each `.md` file to its Notion page ID. Add it to git (so the mapping
travels with the project) or `.gitignore` it if you'd rather not track it
— either works.

---

## The basic loop

### Push a new file (creates a Notion page, captures its ID)

```bash
notion-sync push report.md
# → created report.md -> 361d9fdd-...
```

The Notion page title comes from the `# Heading` on the first line of the
file (Enhanced Markdown convention). If you want a specific title, lead the
file with `# Your Title`. Otherwise the file is created with title "Untitled".

### Push an existing file (updates the page in place)

```bash
notion-sync push report.md
# → updated report.md -> 361d9fdd-...
```

The script looks up the page ID in `.notion-sync.tsv`. If found, it calls
`ntn pages update` instead of `ntn pages create`.

### Pull a page back to local markdown

```bash
notion-sync pull report.md
# → pulled 361d9fdd-... -> report.md
```

Overwrites the local file with the Notion page's current content (Enhanced
Markdown, including a `--- title: ... ---` frontmatter block from the page
properties). Use this to bring Notion-side edits back into your repo.

### See what's tracked

```bash
notion-sync list
# report.md       361d9fdd-1a1a-81d9-bdd7-e7c5434899dd
# notes/q3.md     361d9fdd-1a1a-8178-b682-e3dac4d74c4d
```

---

## Pushing multiple files

There's no built-in batch command — use a shell loop:

```bash
# Push every markdown file in the current directory
for f in *.md; do notion-sync push "$f"; done

# Or for a tree, pick the files you actually want to sync (skip drafts/notes/.etc):
find docs/ -name '*.md' -not -name '_*' -print0 | xargs -0 -n1 notion-sync push
```

Every file becomes a direct child of `NOTION_SYNC_ROOT`. The script does not
mirror directory hierarchy into a Notion page tree — all tracked files are
siblings under the same root page. (If you want nested pages, push the
parents first, then pass their `--parent` explicitly for nested files. But
that complicates the model and isn't supported by the env-var default.)

---

## Uploading files referenced in markdown (images, PDFs, etc.)

If your markdown has `![alt](./diagram.png)` style references, those don't
get uploaded automatically by `ntn pages create`. Two paths:

### Path 1: Upload first, then reference by URL

```bash
# Upload the file, capture the upload id
UPLOAD=$(notion-sync upload diagram.png | awk '{print $1}')
# Then in your markdown, reference the resulting Notion file URL.
```

The `upload` subcommand automatically renames code/config files (`.py`,
`.sh`, `.md`, `.yaml`, etc.) to `.txt` before uploading, because Notion's
File Upload API rejects those extensions with `400 validation_error`. The
content is unchanged; only the filename gets the suffix.

### Path 2: Host files externally

For images already on the web, just reference the public URL in your
markdown — `ntn pages create` will accept `![alt](https://...)` and produce
an external image block, no upload needed.

### Path 3: Don't bother — keep media in the file

If your "report" is just text + code, none of this applies. Skip.

---

## Updating: what `ntn pages update` actually does

`notion-sync push <file>` for an already-tracked file runs:

```bash
ntn pages update <page-id> < file.md
```

This **replaces the page content** with the new markdown. However, ntn
refuses to do this if it would orphan child pages under the page — you'll
see:

```
error: 400 validation_error: This operation would delete N child page(s) or database(s):
  - page: "Name" (id: ...)
To proceed, either:
  1. Include these items in content using <page url="..."> or <database url="..."> tags, OR
  2. Pass --allow-deleting-content
```

For the "flat sub-pages under one root" model assumed here, this rarely
trips — your synced files are leaf pages, not parents of other pages. If
you do hit it, either:

- Edit the markdown to reference the child as `<page url="https://www.notion.so/<id>"/>`, or
- Manually run `ntn pages update <id> --allow-deleting-content < file.md` to trash the orphaned children (recoverable from Notion's trash).

The helper doesn't expose `--allow-deleting-content` deliberately — it's
destructive and shouldn't be the default. If you need it, call ntn directly.

---

## What if I edit the Notion page in the browser?

The script does not detect drift. If you `push` after a Notion-side edit,
your local file overwrites the Notion edits. Two ways to handle it:

- **Pull-first habit**: `notion-sync pull report.md` before editing locally, then push.
- **Treat one side as source of truth**: edit local only, or edit Notion only and pull periodically.

For generated reports (notebooks emitting markdown), local-as-source-of-truth
is the natural model — Notion is the display layer, not the editor.

---

## Pulling everything tracked

To refresh all local files from Notion (e.g. after collaborator edits):

```bash
awk -F'\t' '{print $1}' .notion-sync.tsv | while read -r f; do
  notion-sync pull "$f"
done
```

---

## Forgetting / re-pointing a file

`.notion-sync.tsv` is just a TSV. Edit it directly to:

- **Untrack a file** (without deleting the Notion page): delete the line.
- **Re-point a file to a different Notion page**: change the second column.
- **Rename a file locally**: change the first column to match the new path.

If you want to also trash the Notion page itself when untracking:

```bash
id=$(awk -F'\t' '$1=="report.md"{print $2}' .notion-sync.tsv)
NOTION_KEYRING=0 ntn pages trash --yes "$id"
sed -i '/^report\.md\t/d' .notion-sync.tsv
```

---

## Gotchas

- **Title source**: the page title is taken from the first `# Heading` in
  your markdown. If you don't have one, the title will be "Untitled".
- **Bidirectional sync is not three-way**: `pull` overwrites local, `push`
  overwrites remote. There is no conflict detection or merge. Treat one
  direction as authoritative or pull-before-edit.
- **Enhanced Markdown quirks**: callouts, highlights, wiki-links, and
  footnotes require specific syntax (or don't work at all). See
  `obsidian-to-enhanced-markdown.md` (alongside) for the full translation reference.
- **Page ID stability**: ntn returns canonical UUIDs (`xxxxxxxx-xxxx-...`).
  The script stores them as returned. If you copy an ID from a Notion URL
  manually, it'll be unhyphenated — ntn handles both forms transparently.
- **Auth on headless boxes**: every shell that runs `ntn` needs
  `NOTION_KEYRING=0` if the keychain isn't writable. Easiest: export it once
  in `~/.bashrc` / `~/.zshrc`.

---

## Without the helper (raw `ntn` equivalents)

The helper is a thin wrapper. The equivalents using `ntn` directly:

```bash
ROOT=361d9fdd-1a1a-8052-abf3-da510deb5102

# First push — capture the id yourself
ID=$(NOTION_KEYRING=0 ntn pages create --parent "page:$ROOT" --json < report.md | jq -r .id)
echo "$ID" > .report.id

# Update
NOTION_KEYRING=0 ntn pages update "$(cat .report.id)" < report.md

# Pull
NOTION_KEYRING=0 ntn pages get "$(cat .report.id)" > report.md

# Upload a code file (manual workaround)
NOTION_KEYRING=0 ntn files create --filename script.py.txt --content-type text/plain < script.py
```

The only thing the helper adds is the TSV sidecar so you don't keep
re-typing or losing page IDs, plus auto-applying the `.txt` workaround
on uploads.

---

## End-to-end example

```bash
# One-time
export NOTION_KEYRING=0
export NOTION_SYNC_ROOT=https://www.notion.so/yourws/Reports-361d9fdd1a1a8052abf3da510deb5102
ntn login

# Daily workflow: generate report, push, share the URL
python generate_report.py > report.md
notion-sync push report.md
# → created report.md -> 361d9fdd-1a1a-...
# Share the page URL from Notion's UI or fish it out of `ntn api v1/pages/<id>`.

# Next day: regenerate, push updates the same page
python generate_report.py > report.md
notion-sync push report.md
# → updated report.md -> 361d9fdd-1a1a-...

# Co-worker edited in Notion; bring it back
notion-sync pull report.md

# Add a second report
python generate_q2.py > q2.md
notion-sync push q2.md
# → created q2.md -> ... (also under NOTION_SYNC_ROOT)

notion-sync list
# report.md    361d9fdd-1a1a-...
# q2.md        361d9fdd-1a1a-...
```
