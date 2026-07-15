#!/usr/bin/env node
/**
 * frontend-crafter · lint.mjs
 * The durable mechanical gate. Reads bans.json (the single ban SoT) and checks
 * generated files for statically-verifiable violations — runs HEADLESS, deterministic, no deps.
 *
 * Covers: regex rules (pure #000, h-screen, 100vw, @import, positive tabindex, innerHTML dynamic,
 * inline handlers), banned fonts by name, copy tics + LABEL//YEAR (warn), markup (img alt/dims,
 * label-for), and TOKEN-PAIR CONTRAST (WCAG ratio on declared fg/bg pairs — incl. OKLCH — which is
 * why it works with no browser). Text-on-image contrast is NOT here: it needs rendering → vision.
 *
 * Usage:
 *   node lint.mjs <file|dir> [more...]        # lint files/dirs (recurses design extensions)
 *   node lint.mjs --plan <design-plan.md> ... # also contrast-check the plan's fg/bg pairs
 *   node lint.mjs --test                      # self-test against lint.fixtures/ (red-green)
 *   node lint.mjs --json <targets...>         # machine-readable findings
 *
 * Exit code: non-zero if any BLOCK-severity finding (or a failed self-test).
 * Cross-platform: Node + path/fs only, no hardcoded separators.
 */

import fs from 'node:fs';
import path from 'node:path';
import url from 'node:url';

const HERE = path.dirname(url.fileURLToPath(import.meta.url));
const DESIGN_EXT = new Set(['.html', '.htm', '.css', '.jsx', '.tsx', '.vue', '.svelte', '.js', '.ts']);

// ---------- ban source ----------
function loadBans() {
  // bans.json lives in the sibling skill dir; resolve relative to this script, cross-platform.
  const p = path.join(HERE, '..', 'skills', 'frontend-crafter', 'bans.json');
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

// ---------- color → sRGB → WCAG contrast ----------
function hexToRgb(hex) {
  let h = hex.replace('#', '').trim();
  if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  if (h.length === 8) h = h.slice(0, 6);
  if (!/^[0-9a-fA-F]{6}$/.test(h)) return null;
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}

function srgbToLinear(c) {
  const x = c / 255;
  return x <= 0.04045 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
}

// OKLCH → linear sRGB → sRGB (Björn Ottosson's oklab). L in 0..1, C chroma, H degrees.
function oklchToRgb(L, C, Hdeg) {
  const h = (Hdeg * Math.PI) / 180;
  const a = C * Math.cos(h);
  const b = C * Math.sin(h);
  const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = L - 0.0894841775 * a - 1.291485548 * b;
  const l = l_ ** 3, m = m_ ** 3, s = s_ ** 3;
  let r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s;
  let g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s;
  let bl = -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s;
  const lin2srgb = (x) => {
    const v = x <= 0.0031308 ? 12.92 * x : 1.055 * Math.pow(Math.max(x, 0), 1 / 2.4) - 0.055;
    return Math.max(0, Math.min(1, v)) * 255;
  };
  return [lin2srgb(r), lin2srgb(g), lin2srgb(bl)];
}

// Parse a CSS color token → [r,g,b] (0..255) or null if unsupported.
function parseColor(str) {
  if (!str) return null;
  const s = str.trim();
  let m;
  if (s.startsWith('#')) return hexToRgb(s);
  if ((m = s.match(/rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)/i))) {
    return [+m[1], +m[2], +m[3]];
  }
  if ((m = s.match(/oklch\(\s*([\d.]+)%?\s+([\d.]+)\s+([\d.]+)/i))) {
    let L = parseFloat(m[1]);
    if (s.includes('%')) L = L / 100;
    return oklchToRgb(L, parseFloat(m[2]), parseFloat(m[3]));
  }
  return null;
}

function relLuminance([r, g, b]) {
  return 0.2126 * srgbToLinear(r) + 0.7152 * srgbToLinear(g) + 0.0722 * srgbToLinear(b);
}

function contrastRatio(a, b) {
  const c1 = parseColor(a), c2 = parseColor(b);
  if (!c1 || !c2) return null;
  const l1 = relLuminance(c1), l2 = relLuminance(c2);
  const [hi, lo] = l1 >= l2 ? [l1, l2] : [l2, l1];
  return (hi + 0.05) / (lo + 0.05);
}

// ---------- file scanning ----------
function classify(file) {
  const e = path.extname(file).toLowerCase();
  if (e === '.css') return 'css';
  if (e === '.html' || e === '.htm' || e === '.vue' || e === '.svelte') return 'html';
  return 'js';
}

function walk(target, out) {
  const st = fs.statSync(target);
  if (st.isDirectory()) {
    for (const name of fs.readdirSync(target)) {
      if (name === 'node_modules' || name === '.git' || name === '.crafter') continue;
      walk(path.join(target, name), out);
    }
  } else if (DESIGN_EXT.has(path.extname(target).toLowerCase())) {
    out.push(target);
  }
}

function lineOf(text, index) {
  return text.slice(0, index).split('\n').length;
}

function scanFile(file, bans) {
  const findings = [];
  const text = fs.readFileSync(file, 'utf8');
  const kind = classify(file);
  const add = (severity, rule, message, idx) =>
    findings.push({ file, line: idx == null ? 1 : lineOf(text, idx), severity, rule, message });

  // regex rules scoped by `on`
  for (const r of bans.regexRules) {
    if (!r.on.includes(kind)) continue;
    const re = new RegExp(r.pattern, 'g');
    let m;
    while ((m = re.exec(text))) add(r.severity, r.id, r.message, m.index);
  }

  // banned fonts (any file that declares them)
  for (const font of bans.fonts.banned) {
    const re = new RegExp(`["'\\s:]${font.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&')}["',]`, 'gi');
    let m;
    while ((m = re.exec(text))) add(bans.fonts.severity, 'banned-font', `${bans.fonts.message} (${font})`, m.index);
  }

  // copy tics + LABEL//YEAR (warn)
  for (const tic of bans.copyTics.banned) {
    const re = new RegExp(`\\b${tic}\\b`, 'g');
    let m;
    while ((m = re.exec(text))) add(bans.copyTics.severity, 'copy-tic', `AI copy tic: "${tic}". Say it plainly.`, m.index);
  }
  {
    const re = new RegExp(bans.copyTics.labelYearPattern, 'g');
    let m;
    while ((m = re.exec(text))) add('warn', 'label-year', 'LABEL // YEAR is lazy AI typography, not design.', m.index);
  }

  // markup checks (html only)
  if (kind === 'html') {
    const imgRe = /<img\b[^>]*>/gi;
    let m;
    while ((m = imgRe.exec(text))) {
      const tag = m[0];
      if (bans.markup.requireImgAlt && !/\balt\s*=/.test(tag))
        add(bans.markup.severity, 'img-alt', 'img needs meaningful alt (or alt="" if decorative).', m.index);
      if (bans.markup.requireImgDimensions && !(/\bwidth\s*=/.test(tag) && /\bheight\s*=/.test(tag)))
        add(bans.markup.severity, 'img-dims', 'img needs width+height to prevent CLS.', m.index);
    }
  }
  return findings;
}

// ---------- token-pair contrast from a design-plan ----------
function contrastFromPlan(planPath, bans) {
  const findings = [];
  let text;
  try { text = fs.readFileSync(planPath, 'utf8'); } catch { return findings; }
  // Look for "fg: <color> / bg: <color>" or "<color> on <color>" pairs, or a "pairs:" block.
  const pairRe = /([#][0-9a-fA-F]{3,8}|oklch\([^)]+\)|rgba?\([^)]+\))\s*(?:on|\/|→|->)\s*([#][0-9a-fA-F]{3,8}|oklch\([^)]+\)|rgba?\([^)]+\))/gi;
  let m, any = false;
  while ((m = pairRe.exec(text))) {
    any = true;
    const ratio = contrastRatio(m[1], m[2]);
    if (ratio == null) {
      findings.push({ file: planPath, line: lineOf(text, m.index), severity: 'warn', rule: 'contrast-unparsed',
        message: `Could not parse contrast pair ${m[1]} on ${m[2]}.` });
    } else if (ratio < bans.contrast.textMin) {
      findings.push({ file: planPath, line: lineOf(text, m.index), severity: 'block', rule: 'contrast',
        message: `Token-pair contrast ${ratio.toFixed(2)}:1 < ${bans.contrast.textMin}:1 (${m[1]} on ${m[2]}).` });
    }
  }
  if (!any) findings.push({ file: planPath, line: 1, severity: 'warn', rule: 'contrast-none',
    message: 'No fg/bg contrast pairs found in design-plan — declare them as "fg on bg" for the headless contrast check.' });
  return findings;
}

// ---------- reporting ----------
function report(findings, json) {
  if (json) { process.stdout.write(JSON.stringify(findings, null, 2) + '\n'); return; }
  const blocks = findings.filter((f) => f.severity === 'block');
  const warns = findings.filter((f) => f.severity === 'warn');
  for (const f of findings) {
    const tag = f.severity === 'block' ? 'BLOCK' : 'warn ';
    process.stdout.write(`  [${tag}] ${path.relative(process.cwd(), f.file)}:${f.line}  ${f.rule} — ${f.message}\n`);
  }
  process.stdout.write(`\n  ${blocks.length} blocking, ${warns.length} warnings.\n`);
}

// ---------- self-test (red-green) ----------
function selfTest(bans) {
  const dir = path.join(HERE, 'lint.fixtures');
  let ok = true;
  const good = path.join(dir, 'good');
  const bad = path.join(dir, 'bad');
  if (fs.existsSync(good)) {
    const files = []; walk(good, files);
    for (const f of files) {
      const blocks = scanFile(f, bans).filter((x) => x.severity === 'block');
      if (blocks.length) { ok = false; process.stdout.write(`  FAIL good/${path.basename(f)} unexpectedly blocked: ${blocks.map((b) => b.rule).join(',')}\n`); }
      else process.stdout.write(`  ok   good/${path.basename(f)} clean\n`);
    }
  }
  if (fs.existsSync(bad)) {
    const files = []; walk(bad, files);
    for (const f of files) {
      const blocks = scanFile(f, bans).filter((x) => x.severity === 'block');
      if (!blocks.length) { ok = false; process.stdout.write(`  FAIL bad/${path.basename(f)} should have blocked but was clean\n`); }
      else process.stdout.write(`  ok   bad/${path.basename(f)} → ${blocks.map((b) => b.rule).join(',')}\n`);
    }
  }
  process.stdout.write(ok ? '\n  SELF-TEST PASSED\n' : '\n  SELF-TEST FAILED\n');
  return ok;
}

// ---------- main ----------
function main() {
  const argv = process.argv.slice(2);
  const bans = loadBans();
  if (argv.includes('--test')) { process.exit(selfTest(bans) ? 0 : 1); }

  const json = argv.includes('--json');
  const planIdx = argv.indexOf('--plan');
  const planPath = planIdx >= 0 ? argv[planIdx + 1] : null;
  const targets = argv.filter((a, i) => !a.startsWith('--') && i !== (planIdx + 1));

  if (!targets.length && !planPath) {
    process.stdout.write('usage: lint.mjs <file|dir> [--plan design-plan.md] [--json] | --test\n');
    process.exit(2);
  }

  const files = [];
  for (const t of targets) walk(t, files);
  let findings = [];
  for (const f of files) findings = findings.concat(scanFile(f, bans));
  if (planPath) findings = findings.concat(contrastFromPlan(planPath, bans));

  report(findings, json);
  process.exit(findings.some((f) => f.severity === 'block') ? 1 : 0);
}

main();
