---
name: handoff-pdf
description: Regenerate a styled solution-design PDF (e.g. Client-Handoff.pdf) from its Markdown source, reproducing the house style of the original handoff PDFs — navy headings with rules, justified body, dark-navy table headers, alternating row shading. Use whenever a solution-design/*.md changes and its PDF deliverable needs to be rebuilt.
---

<what-to-do>

Rebuild the PDF deliverable from its Markdown source while preserving the exact
house style of the original handoff PDFs.

Run the bundled build script — it handles dependencies, HTML rendering, and the
headless-Chrome print step:

```bash
bash .claude/skills/handoff-pdf/build-pdf.sh solution-design/Client-Handoff.md
```

This writes `solution-design/Client-Handoff.pdf` next to the source. To target a
different output path, pass it as the second argument:

```bash
bash .claude/skills/handoff-pdf/build-pdf.sh <input.md> <output.pdf>
```

After building, verify the result before reporting done:

```bash
pdftoppm -png -r 110 solution-design/Client-Handoff.pdf /tmp/check
```

Then Read the `/tmp/check-*.png` images and confirm the styling matches the
original (navy title + 2px underline, navy section headings with light rules,
justified slate body text, navy bold inline terms, navy-header table with
alternating row shading). Mention page count and any table page-break behavior.

</what-to-do>

<supporting-info>

## How it works

- `render.js` — converts Markdown to HTML with `marked` and injects the house
  stylesheet. The CSS tokens were sampled pixel-by-pixel from
  `solution-design/Client-Handoff-original.pdf`; do not change them unless the
  house style itself changes. The PDF title is derived from the first `# H1`.
- `build-pdf.sh` — ensures `marked` is installed (vendored in this skill dir),
  finds a Chrome/Chromium binary, renders the HTML, and prints to PDF with the
  same engine (`--headless ... --print-to-pdf`) used for the originals.

## Style tokens (for reference)

| Token | Hex | Used for |
|---|---|---|
| navy | `#0F2A4A` | title, headings, bold inline, table header bg, bullets, blockquote bar |
| slate | `#1F2937` | body text |
| shade | `#F4F7FA` | table even-row stripe, blockquote background |
| border | `#D3DCE6` | H2 underline, table cell borders |

Body: Helvetica Neue, 10pt, line-height 1.6, justified. Page: US Letter, 0.7in
margins. First table column: 42% width.

## Markdown conventions that render correctly

- The first `# Heading` becomes the title (navy, 2px underline) and the PDF title.
- An italic line immediately after the title (`*...*`) renders as a muted subtitle.
- `**bold**` lead-ins render in navy; GFM tables get the navy header + striping.
- A `> blockquote` renders as the light-blue summary box with a navy left bar.

## Requirements

Node.js (for `marked`), a Chrome/Chromium install, and `pdftoppm` (poppler) for
verification. No always-on services.

</supporting-info>
