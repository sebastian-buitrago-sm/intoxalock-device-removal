#!/usr/bin/env node
/*
 * render.js — Markdown -> styled HTML for the Intoxalock client-handoff deliverables.
 *
 * The CSS below reproduces the visual design of the original
 * solution-design/Client-Handoff PDF. Style tokens were sampled directly from
 * that PDF and should not be changed unless the house style itself changes.
 *
 * Usage: node render.js <input.md> <output.html>
 */
const fs = require('fs');

// Resolve `marked` from CWD or the skill's own node_modules (build-pdf.sh installs it here).
let marked;
for (const p of ['marked', require('path').join(__dirname, 'node_modules', 'marked')]) {
  try { marked = require(p).marked; break; } catch (_) {}
}
if (!marked) {
  console.error('ERROR: `marked` not found. Run build-pdf.sh, or `npm install marked@15` here.');
  process.exit(1);
}

const [, , mdPath, outPath] = process.argv;
if (!mdPath || !outPath) {
  console.error('Usage: node render.js <input.md> <output.html>');
  process.exit(1);
}

const md = fs.readFileSync(mdPath, 'utf8');
marked.setOptions({ gfm: true, breaks: false });
const body = marked.parse(md);

// Derive the <title> from the first H1 so the PDF metadata title is correct.
const h1 = (md.match(/^\s*#\s+(.+?)\s*$/m) || [, 'Solution Handoff'])[1].replace(/[#*_`]/g, '');

// --- House style (sampled from Client-Handoff-original.pdf) ---
//   navy   #0F2A4A : title, section headings, bold inline, table header, bullets, blockquote bar
//   slate  #1F2937 : body text
//   shade  #F4F7FA : table even-row stripe, blockquote background
//   border #D3DCE6 : H2 underline, table cell borders
const css = `
  @page { size: letter; margin: 0.7in; }
  * { box-sizing: border-box; }
  html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  body {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.6;
    color: #1F2937;
    margin: 0;
    text-align: justify;
    -webkit-font-smoothing: antialiased;
  }
  h1 {
    color: #0F2A4A;
    font-weight: 700;
    font-size: 20pt;
    line-height: 1.2;
    margin: 0 0 0.18in 0;
    padding-bottom: 10px;
    border-bottom: 2px solid #0F2A4A;
    text-align: left;
    letter-spacing: -0.2px;
  }
  /* italic subtitle directly under the title */
  h1 + p {
    font-style: italic;
    color: #5B6573;
    font-size: 10.5pt;
    margin: -0.04in 0 0.28in 0;
    text-align: left;
  }
  h2 {
    color: #0F2A4A;
    font-weight: 700;
    font-size: 13.5pt;
    margin: 0.34in 0 0.12in 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #D3DCE6;
    text-align: left;
  }
  p { margin: 0 0 0.14in 0; }
  strong { color: #0F2A4A; font-weight: 700; }
  em { font-style: italic; }
  ul { margin: 0 0 0.14in 0; padding-left: 0.26in; }
  li { margin: 0 0 0.08in 0; padding-left: 0.04in; }
  li::marker { color: #0F2A4A; }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.06in 0 0.2in 0;
    font-size: 10pt;
  }
  th {
    background: #0F2A4A;
    color: #ffffff;
    font-weight: 700;
    text-align: left;
    padding: 9px 12px;
    border: 1px solid #0F2A4A;
    vertical-align: top;
  }
  td {
    padding: 9px 12px;
    border: 1px solid #D3DCE6;
    vertical-align: top;
    text-align: left;
  }
  tbody tr:nth-child(even) { background: #F4F7FA; }
  tbody tr:nth-child(odd)  { background: #ffffff; }
  th:first-child, td:first-child { width: 42%; }
  blockquote {
    background: #F4F7FA;
    border-left: 4px solid #0F2A4A;
    margin: 0.2in 0;
    padding: 0.12in 0.2in;
    color: #1F2937;
    text-align: left;
  }
  blockquote p { margin: 0; }
  a { color: #0F2A4A; text-decoration: none; }
`;

const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>${h1}</title>
<style>${css}</style>
</head>
<body>
${body}
</body>
</html>`;

fs.writeFileSync(outPath, html);
console.log('wrote', outPath);
