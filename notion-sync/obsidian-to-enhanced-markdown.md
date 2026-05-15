# Obsidian → Notion Enhanced Markdown translation

Reference for converting Obsidian-flavored markdown (or any non-standard markdown
narko historically handled) into the [Enhanced Markdown](https://developers.notion.com/guides/data-apis/enhanced-markdown)
format that `ntn pages create` / `ntn pages update` consume.

All syntax behaviors below were verified empirically against `ntn 0.14.0` and the
live Notion API. Where the spec and the implementation disagreed, the
implementation is what's documented.

---

## Quick-reference translation table

| Obsidian / Marko / GFM input            | Enhanced Markdown output                                 | Notion result                          |
| --------------------------------------- | -------------------------------------------------------- | -------------------------------------- |
| `> [!NOTE] Title`<br>`> body`           | `<callout icon="ℹ️" color="blue">`<br>`body`<br>`</callout>` | Callout block, blue, info icon         |
| `> [!WARNING]`<br>`> body`              | `<callout icon="⚠️" color="yellow">…</callout>`         | Callout, yellow, warning icon          |
| `==highlighted==`                       | `<span color="yellow_bg">highlighted</span>`            | Yellow-background highlight annotation |
| `[[Page Name]]`                         | `<mention-page url="https://notion.so/<page-id>">Page Name</mention-page>` | Notion page mention link |
| `[[Page Name\|alias]]`                  | `<mention-page url="…">alias</mention-page>`             | Mention link with custom label         |
| `![[image.png]]`                        | `![image.png](attachment-url-or-path)`                   | Image block (after uploading the file via `ntn files create`) |
| `#tag`                                  | (no equivalent — leave as literal text or use a mention) | Plain text                             |
| `[^1]` footnote ref + `[^1]: body`      | (not supported — dropped)                                | Refs become `[1]` literal text         |
| `~~strikethrough~~`                     | `~~strikethrough~~` (unchanged — GFM works)             | Strikethrough annotation               |
| `- [x] task`                            | `- [x] task` (unchanged)                                 | To-do block, checked                   |
| `\| col \| col \|` GFM table            | unchanged — pipe tables work                             | Table with `has_column_header: true`   |
| `$$E = mc^2$$`                          | unchanged                                                | Inline equation rich-text              |
| `$x^2$`                                 | unchanged                                                | Inline equation rich-text              |
| `` ```python … ``` ``                   | unchanged                                                | Code block with language               |

---

## What works as-is (no translation needed)

These pass through unchanged from CommonMark / GFM / Obsidian to Enhanced
Markdown:

- **Headings** `#` … `######`
- **Paragraphs**, blank-line-separated
- **Bold** `**text**`, **italic** `*text*`, **inline code** `` `text` ``
- **Strikethrough** `~~text~~` (verified: produces `strikethrough: true` annotation)
- **Code blocks** with language fences (` ```python ` etc.) — Notion supports 80+ languages
- **Bullet/ordered lists** `-` / `*` / `1.`
- **Task lists** `- [x]` / `- [ ]` — produce `to_do` blocks
- **GFM pipe tables** — produce `table` blocks with `has_column_header: true` derived from the `|---|` separator row
- **Math** — placement matters:
  - `$inline$` → inline equation rich-text
  - `$$E = mc^2$$` on a **single line** → inline equation rich-text inside a paragraph
  - `$$` / `E = mc^2` / `$$` on **separate lines** → standalone `equation` block. Use the multi-line form when you want a block-level equation.
- **Links** `[label](url)` — for external URLs and absolute Notion URLs
- **Images** `![alt](url)` — for hosted URLs; for local files use `ntn files create` first then reference the returned attachment URL
- **Blockquotes** `> text` — produce `quote` blocks (note: this is exactly what consumes the Obsidian callout syntax)
- **Frontmatter** YAML — `ntn pages get` adds it; `ntn pages create` accepts it (used for properties when the parent is a database)

---

## Translations required

### Callouts (must convert)

Obsidian uses `> [!TYPE]` blockquote callouts:

```markdown
> [!NOTE] Optional title
> Body line 1
> Body line 2
```

Enhanced Markdown requires `<callout>` XML tags. The Obsidian syntax falls
through as a plain quote block with `[!NOTE]` left as visible text.

```markdown
<callout icon="ℹ️" color="blue">
Body line 1
Body line 2
</callout>
```

**Mapping** of Obsidian callout types to a reasonable icon + color:

| Obsidian type    | icon  | color         |
| ---------------- | ----- | ------------- |
| `[!NOTE]`        | `ℹ️`  | `blue`        |
| `[!ABSTRACT]` / `[!SUMMARY]` / `[!TLDR]` | `📋` | `blue` |
| `[!INFO]` / `[!TODO]` | `ℹ️` | `blue` |
| `[!TIP]` / `[!HINT]` / `[!IMPORTANT]` | `💡` | `green` |
| `[!SUCCESS]` / `[!CHECK]` / `[!DONE]` | `✅` | `green` |
| `[!QUESTION]` / `[!HELP]` / `[!FAQ]` | `❓` | `purple` |
| `[!WARNING]` / `[!CAUTION]` / `[!ATTENTION]` | `⚠️` | `yellow` |
| `[!FAILURE]` / `[!FAIL]` / `[!MISSING]` | `❌` | `red` |
| `[!DANGER]` / `[!ERROR]`               | `🔥` | `red` |
| `[!BUG]`         | `🐛`  | `red`         |
| `[!EXAMPLE]`     | `📝`  | `purple`      |
| `[!QUOTE]` / `[!CITE]` | `💬` | `gray` |

**Quirks**:

- `color` must be **lowercase**: `blue`, not `Blue`. (Empirically: `color="Blue"` is sent but Notion returns `color: "default"` — the value gets silently dropped.)
- Foldable callouts (`> [!NOTE]+` / `> [!NOTE]-` for default-open / default-closed) — no Enhanced Markdown equivalent. Falls back to a non-foldable callout. If foldability matters, use a Notion toggle block instead.
- Custom Obsidian callout types defined via CSS — won't translate. Map to a sensible default (`📌` icon, `gray` color).
- Callouts can contain multiple blocks and nested children, including other callouts. Indent nested content with tabs (Enhanced Markdown uses tabs for hierarchy, not spaces).

### Highlights (must convert)

Obsidian default:

```markdown
This is ==highlighted== text.
```

Enhanced Markdown has no `==` syntax; use a color span:

```markdown
This is <span color="yellow_bg">highlighted</span> text.
```

**Quirks**:

- Color names must be **lowercase**. The supported set is `gray`, `brown`, `orange`, `yellow`, `green`, `blue`, `purple`, `pink`, `red`.
- Append `_bg` for background (highlight). Without `_bg` you get colored *text* foreground.
- The Notion API stores these as `color: "yellow_background"` etc.; the Enhanced Markdown abbreviates `_background` to `_bg`.
- Case sensitivity is the gotcha: `<span color="Yellow_bg">` is silently dropped (sent, but returned annotations show `color: "default"`).

### Wiki links (must convert if you have any)

Obsidian default:

```markdown
See [[Other Page]] for details.
See [[Other Page|the other page]] for details (with alias).
```

Enhanced Markdown uses `<mention-page>`:

```markdown
See <mention-page url="https://www.notion.so/Other-Page-abc123def…">Other Page</mention-page> for details.
See <mention-page url="https://www.notion.so/Other-Page-abc123def…">the other page</mention-page> for details.
```

**Quirks**:

- Requires the **Notion page URL**, not the Obsidian page name. You need a mapping of Obsidian-name → Notion-URL (typically tracked alongside your sync metadata in `.notion-sync.tsv` or similar).
- The label text between the tags is what's displayed; the URL is the target.
- Self-closing form `<mention-page url="…"/>` also works; Notion will use the target page's title as the label.
- Cross-page heading anchors (`[[Other Page#Heading]]`) — no Enhanced Markdown equivalent. Strip to plain `<mention-page>` to the parent page.
- Block references (`[[Other Page#^block-id]]`) — no Enhanced Markdown equivalent. Same fallback.

### Embedded notes (must convert or drop)

Obsidian transclusion:

```markdown
![[Other Note]]            # embed the entire note inline
![[Other Note#Section]]    # embed a section
```

Enhanced Markdown has no transclusion. Closest equivalents:

- Convert to a `<mention-page url="…"/>` link, losing the inline content embed.
- Or manually expand the embedded content into the target page (not automatable without a vault index).

### Embedded files / images (Obsidian wiki-style)

If Obsidian is configured to use wiki-style file embeds:

```markdown
![[diagram.png]]
```

Enhanced Markdown expects standard markdown image syntax, with a URL that
points to a file already uploaded to Notion:

```markdown
![diagram.png](https://prod-files-secure.s3.us-west-2.amazonaws.com/…)
```

Workflow:

1. Upload local file: `UPLOAD_ID=$(ntn files create --filename diagram.png < diagram.png | jq -r .id)`
2. Reference the upload by attaching it during page creation (or use the upload ID directly per the [files API docs](https://developers.notion.com/reference/file-upload)).
3. For unsupported extensions (`.py`, `.sh`, `.md`, etc.), rename to `.txt` first: `--filename diagram.py.txt`. See `notion-sync.sh upload` for the auto-rename helper.

### Footnotes (not supported)

Standard footnote syntax (`[^1]` / `[^1]: body`) does not work. The reference is
mangled to `[1]` literal text, the name is lost (`[^methods]` and `[^1]` both
become `[1]`), and the definition becomes an orphan paragraph. If you need
citations, rewrite them inline or as a separate references section before
sending to ntn.

### Hashtags (lossy)

Obsidian `#tag` and `#nested/tag` syntax has no Notion equivalent in
Enhanced Markdown. They survive as plain `#tag` text (the `#` doesn't get
parsed as a heading because it's not at start-of-line).

If tags are meaningful, the options are:

- **Best**: turn each tag into a Notion page and reference via `<mention-page>`.
- **Acceptable**: leave as literal `#tag` text.
- **Notion-native**: if the target Notion page is in a database, push tags through frontmatter as a multi-select property.

### Comments (drop)

Obsidian `%% comment %%` syntax — no Enhanced Markdown equivalent. Strip
before sending; ntn will render them as literal `%%` text.

---

## Obsidian config recommendations

Obsidian settings that reduce translation burden:

### Settings → Files & Links

- **"Use [[Wikilinks]]"** → **OFF**. With this off, internal links use standard markdown `[label](Other-Note.md)` instead of `[[Other Note]]`. The translator still needs to rewrite the `.md` target to a Notion URL, but the syntax matches Enhanced Markdown's expectation of standard markdown link syntax.
- **"New link format"** → **Absolute path in vault** (if wikilinks are on). Makes wikilink resolution deterministic, easier to map to Notion URLs.
- **"Default location for new attachments"** → keep all attachments under a single subfolder. Makes file-upload preprocessing simpler.

### Settings → Editor

- **"Strict line breaks"** → **ON** to match CommonMark. (Obsidian's default is "off" which treats single newlines as line breaks; Enhanced Markdown is CommonMark-strict.)
- **"Show frontmatter"** → ON, so YAML frontmatter is visible and editable in the source.

### Settings that can't be changed (must be handled by translation)

- Highlights (`==text==`) — no toggle in Obsidian to disable; always converts.
- Callouts (`> [!TYPE]`) — no toggle; always converts.
- Tags (`#tag`) — Obsidian's tag panel relies on them; can't really disable.
- Frontmatter conventions — Obsidian uses `tags:` and `aliases:` in YAML; ntn will pass through unchanged but they won't map to Notion properties unless the target is a database with matching property names.

---

## Putting it together: minimal translation script

A `sed`-style translator can handle the high-frequency cases:

```bash
# Obsidian → Enhanced Markdown, leaves un-translatable parts as-is

input="${1:?usage: translate.sh file.md}"

sed -E '
  # ==highlight==  →  <span color="yellow_bg">highlight</span>
  s/==([^=]+)==/<span color="yellow_bg">\1<\/span>/g

  # > [!NOTE] / [!TIP] / etc.  →  <callout icon="…" color="…">
  # (Multi-line; simple sed only handles the marker line — a real
  #  implementation needs a small state machine for the body collapse.)
' "$input"
```

Callouts and wiki-links need more than a regex pass because their bodies span
multiple lines (callouts) and require an external page-name → Notion-URL
mapping (wiki-links). For a one-shot vault migration, a small Python script
using `python-frontmatter` + a `re.sub` per pattern, plus a JSON lookup table
for wiki-link targets, is the right shape.

---

## Verification

Every syntax claim above was tested via:

```bash
# Authoring:
printf '<test markdown>' | NOTION_KEYRING=0 ntn pages create --parent page:<id> --json | jq -r .id
# Inspection:
NOTION_KEYRING=0 ntn api v1/blocks/<page-id>/children | jq '.results[] | .type, .[.type]'
# Round-trip:
NOTION_KEYRING=0 ntn pages get <page-id>
```

Tests were run against ntn 0.14.0 on 2026-05-14. Re-run against newer ntn
versions if behavior seems off — Enhanced Markdown parsing is actively
evolving.
