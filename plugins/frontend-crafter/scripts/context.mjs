#!/usr/bin/env node
/**
 * frontend-crafter · context.mjs
 * Owns the existing-system crawl (improve-existing) AND Tier-2 persistence I/O.
 * Pure Node, no deps, cross-platform (os.homedir() + path.join, no hardcoded separators).
 *
 * The AGENT writes the per-project Tier-1 sidecar (.crafter/design-system.md, design-plan.md,
 * decisions.md, snapshots/) directly. This script owns Tier-2 (the global registry + memory) and
 * READS Tier-1 on resume (with a drift check).
 *
 * Subcommands (all emit JSON on stdout unless noted):
 *   config                              ensure ~/.frontend-crafter/config.json (create if missing)
 *   crawl   <projectPath>               mode B: crawl an existing repo → {tokens, theming, confidence}
 *   resume  <projectPath>               mode A: read .crafter sidecar + drift-check vs live CSS
 *   register <path> --name N --slug S --direction D --register R --brief "..."   upsert registry + memory
 *   resolve <name>                      resolve "open project N" → {status: unique|none|multiple, ...}
 *   recent  [--similar "brief"] [--n 5] recent directions for anti-repetition bias (unpinned axes)
 *   self-heal <name>                    bounded scan of projects_home for a moved project
 */

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const STORE = path.join(os.homedir(), '.frontend-crafter');
const CONFIG = path.join(STORE, 'config.json');
const PROJECTS = path.join(STORE, 'projects.jsonl');
const MEMORY = path.join(STORE, 'design-memory.jsonl');

const DEFAULT_CONFIG = {
  _format: 1,
  projects_home: path.join(os.homedir(), 'frontend-crafter-projects'),
  renderer: 'chrome-mcp',
  hook_enabled: false,
  auto_git_init: false,
};

// ---------- store helpers ----------
function ensureStore() {
  fs.mkdirSync(STORE, { recursive: true });
  if (!fs.existsSync(CONFIG)) fs.writeFileSync(CONFIG, JSON.stringify(DEFAULT_CONFIG, null, 2) + '\n');
}
function loadConfig() {
  ensureStore();
  return { ...DEFAULT_CONFIG, ...JSON.parse(fs.readFileSync(CONFIG, 'utf8')) };
}
function readJsonl(file) {
  if (!fs.existsSync(file)) return [];
  return fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map((l) => {
    try { return JSON.parse(l); } catch { return null; }
  }).filter((x) => x && !x._format);
}
function appendJsonl(file, obj) {
  ensureStore();
  if (!fs.existsSync(file)) fs.writeFileSync(file, JSON.stringify({ _format: 1 }) + '\n');
  fs.appendFileSync(file, JSON.stringify(obj) + '\n'); // append is atomic enough for single-user
}
function out(obj) { process.stdout.write(JSON.stringify(obj, null, 2) + '\n'); }

// ---------- crawl (mode B) ----------
function listFiles(dir, exts, acc = [], depth = 0) {
  if (depth > 6 || !fs.existsSync(dir)) return acc;
  for (const name of fs.readdirSync(dir)) {
    if (['node_modules', '.git', '.crafter', 'dist', 'build', '.next'].includes(name)) continue;
    const p = path.join(dir, name);
    let st; try { st = fs.statSync(p); } catch { continue; }
    if (st.isDirectory()) listFiles(p, exts, acc, depth + 1);
    else if (exts.includes(path.extname(p).toLowerCase())) acc.push(p);
  }
  return acc;
}

function crawl(projectPath) {
  const cssFiles = listFiles(projectPath, ['.css', '.scss']);
  const jsFiles = listFiles(projectPath, ['.js', '.ts', '.jsx', '.tsx']);
  const tokens = { color: {}, type: {}, space: {}, radius: {} };
  const sources = [];

  // 1) CSS custom properties
  for (const f of cssFiles) {
    const t = fs.readFileSync(f, 'utf8');
    let m; const re = /(--[\w-]+)\s*:\s*([^;]+);/g;
    while ((m = re.exec(t))) {
      const name = m[1], val = m[2].trim();
      if (/color|bg|ink|accent|brand|fg|surface|text/i.test(name) || /#|rgb|oklch|hsl/i.test(val)) tokens.color[name] = val;
      else if (/font|family/i.test(name)) tokens.type[name] = val;
      else if (/space|gap|pad|margin/i.test(name)) tokens.space[name] = val;
      else if (/radius|round/i.test(name)) tokens.radius[name] = val;
    }
    if (Object.keys(tokens.color).length) sources.push('css-vars');
  }

  // 2) tailwind.config theme.extend (best-effort)
  const tw = [...cssFiles, ...jsFiles].find((f) => /tailwind\.config\.(js|ts|cjs|mjs)$/.test(f))
    || listFiles(projectPath, ['.js', '.ts', '.cjs', '.mjs']).find((f) => /tailwind\.config/.test(f));
  let theming = { mechanism: 'unknown', evidence: [] };
  if (tw) {
    const t = fs.readFileSync(tw, 'utf8');
    if (!sources.includes('css-vars')) sources.push('tailwind-config');
    const dm = t.match(/darkMode\s*:\s*['"](class|media)['"]/);
    if (dm) theming = { mechanism: `tailwind-${dm[1]}`, evidence: ['tailwind.config darkMode'] };
    const colorBlock = t.match(/colors\s*:\s*\{([\s\S]*?)\}/);
    if (colorBlock) {
      let m; const re = /['"]?([\w-]+)['"]?\s*:\s*['"](#[0-9a-fA-F]{3,8}|oklch\([^)]+\)|rgb[^'"]+)['"]/g;
      while ((m = re.exec(colorBlock[1]))) tokens.color[`tw.${m[1]}`] = m[2];
    }
  }

  // 3) theming mechanism detection (if not from tailwind)
  const allText = jsFiles.slice(0, 200).map((f) => { try { return fs.readFileSync(f, 'utf8'); } catch { return ''; } }).join('\n');
  if (theming.mechanism === 'unknown') {
    if (/next-themes|ThemeProvider/.test(allText)) theming = { mechanism: 'next-themes', evidence: ['next-themes import'] };
    else if (/\[data-theme/.test(allText + cssFiles.map((f) => { try { return fs.readFileSync(f, 'utf8'); } catch { return ''; } }).join(''))) theming = { mechanism: 'data-theme', evidence: ['[data-theme] selector'] };
  }

  // 4) inline hex frequency fallback (only if no tokens found)
  let confidence = 'high';
  if (!Object.keys(tokens.color).length) {
    const freq = {};
    for (const f of [...cssFiles, ...jsFiles].slice(0, 300)) {
      const t = fs.readFileSync(f, 'utf8');
      let m; const re = /#[0-9a-fA-F]{6}\b/g;
      while ((m = re.exec(t))) freq[m[0]] = (freq[m[0]] || 0) + 1;
    }
    const top = Object.entries(freq).sort((a, b) => b[1] - a[1]).slice(0, 8);
    top.forEach(([hex], i) => (tokens.color[`inline.${i}`] = hex));
    sources.push('inline-hex-frequency');
    confidence = top.length ? 'low' : 'none';
  }

  if (confidence === 'none') {
    return { tokens, theming, sources, confidence,
      fallback: 'zero-token: no existing design system found — propose a muted greenfield direction, flag it in the delta plan.' };
  }
  return { tokens, theming, sources, confidence };
}

// ---------- resume (mode A) ----------
function parseSidecarTokens(md) {
  // Extract "--name: value" pairs from the design-system.md token block(s).
  const tokens = {};
  let m; const re = /(--[\w-]+)\s*:\s*([^\n;]+)/g;
  while ((m = re.exec(md))) tokens[m[1]] = m[2].trim();
  return tokens;
}
function resume(projectPath) {
  const crafterDir = path.join(projectPath, '.crafter');
  const dsPath = path.join(crafterDir, 'design-system.md');
  const statePath = path.join(crafterDir, 'state.json');
  if (!fs.existsSync(dsPath)) return { status: 'no-sidecar', hint: 'not a crafter project; treat as improve-existing or greenfield' };
  const state = fs.existsSync(statePath) ? JSON.parse(fs.readFileSync(statePath, 'utf8')) : {};
  const sidecar = parseSidecarTokens(fs.readFileSync(dsPath, 'utf8'));
  const live = crawl(projectPath).tokens.color;
  // drift: sidecar token whose value diverged from the live CSS var of the same name
  const drift = [];
  for (const [name, val] of Object.entries(sidecar)) {
    if (live[name] && live[name] !== val) drift.push({ token: name, sidecar: val, live: live[name] });
  }
  const versionMismatch = state.crafter_version && state.crafter_version !== currentVersion();
  return { status: 'resumed', state, drift, versionMismatch,
    action: versionMismatch ? 'crafter_version differs — warn + full re-crawl, do not trust sidecar blindly (S7)'
      : (drift.length ? 'sidecar drifted from live code — surface before editing (S7)' : 'sidecar current') };
}
function currentVersion() {
  try {
    const p = path.join(path.dirname(new URL(import.meta.url).pathname), '..', '.claude-plugin', 'plugin.json');
    return JSON.parse(fs.readFileSync(p, 'utf8')).version;
  } catch { return '0'; }
}

// ---------- registry (Tier-2) ----------
function register(projectPath, opts) {
  const cfg = loadConfig();
  const rec = {
    id: opts.id || `${opts.slug || path.basename(projectPath)}-${Date.now().toString(36)}`,
    name: opts.name || path.basename(projectPath),
    slug: opts.slug || path.basename(projectPath),
    path: path.resolve(projectPath),
    direction: opts.direction || null,
    register: opts.register || null,
    brief_gist: opts.brief || null,
    created: new Date().toISOString().slice(0, 10),
    last_touched: new Date().toISOString().slice(0, 10),
    crafter_version: currentVersion(),
  };
  // upsert by path
  const all = readJsonl(PROJECTS).filter((r) => r.path !== rec.path);
  ensureStore();
  fs.writeFileSync(PROJECTS, JSON.stringify({ _format: 1 }) + '\n' + all.concat(rec).map((r) => JSON.stringify(r)).join('\n') + '\n');
  // append memory
  if (rec.direction) appendJsonl(MEMORY, {
    direction: rec.direction, register: rec.register, brief_gist: rec.brief_gist,
    palette_hue: opts.palette_hue || null, type_pairing: opts.type_pairing || null, ts: Date.now(),
  });
  return { registered: rec.id, projects_home: cfg.projects_home };
}

// ---------- name resolution (S8) ----------
function resolve(name) {
  const matches = readJsonl(PROJECTS).filter((r) => r.name === name || r.slug === name);
  if (matches.length === 1) return { status: 'unique', project: matches[0] };
  if (matches.length === 0) return { status: 'none', hint: 'no such project — fall to greenfield with a warning (S8)' };
  return { status: 'multiple', matches: matches.map((r) => ({ id: r.id, path: r.path, direction: r.direction, last_touched: r.last_touched })),
    hint: 'ambiguous — list and ask the owner, never guess (S8)' };
}

// ---------- recent for anti-repetition (S9) ----------
function tokenize(s) { return (s || '').toLowerCase().match(/\w+/g) || []; }
function similarity(a, b) {
  const A = new Set(tokenize(a)), B = new Set(tokenize(b));
  if (!A.size || !B.size) return 0;
  let inter = 0; for (const x of A) if (B.has(x)) inter++;
  return inter / Math.sqrt(A.size * B.size);
}
function recent(similarBrief, n) {
  let mem = readJsonl(MEMORY).slice(-50);
  if (similarBrief) mem = mem.filter((m) => similarity(m.brief_gist, similarBrief) >= 0.2);
  const recentDirs = mem.slice(-n).map((m) => m.direction).filter(Boolean);
  return { recent_directions: recentDirs, note: 'bias only — drop these from candidates on UNPINNED axes (S9); not a hard gate' };
}

// ---------- self-heal (S8) ----------
function selfHeal(name) {
  const cfg = loadConfig();
  const stale = readJsonl(PROJECTS).find((r) => r.name === name || r.slug === name);
  if (!stale) return { status: 'none' };
  const candidates = [];
  for (const sc of listFiles(cfg.projects_home, ['.json'], []).filter((f) => f.endsWith(path.join('.crafter', 'state.json')))) {
    try { const st = JSON.parse(fs.readFileSync(sc, 'utf8')); if (st.id === stale.id) candidates.push(path.dirname(path.dirname(sc))); } catch { /* skip */ }
  }
  if (candidates.length === 1) { register(candidates[0], { ...stale, id: stale.id }); return { status: 'relinked', path: candidates[0] }; }
  return { status: candidates.length ? 'multiple' : 'none', candidates, hint: 'surface to owner, never silently relink (S8)' };
}

// ---------- arg parsing ----------
function flags(argv) {
  const f = {}; for (let i = 0; i < argv.length; i++) if (argv[i].startsWith('--')) { f[argv[i].slice(2)] = argv[i + 1]; i++; } return f;
}

function main() {
  const [cmd, ...rest] = process.argv.slice(2);
  const f = flags(rest);
  const pos = rest.filter((a, i) => !a.startsWith('--') && !(i > 0 && rest[i - 1].startsWith('--')));
  switch (cmd) {
    case 'config': ensureStore(); return out(loadConfig());
    case 'crawl': return out(crawl(pos[0] || process.cwd()));
    case 'resume': return out(resume(pos[0] || process.cwd()));
    case 'register': return out(register(pos[0] || process.cwd(), f));
    case 'resolve': return out(resolve(pos[0]));
    case 'recent': return out(recent(f.similar, parseInt(f.n || '5', 10)));
    case 'self-heal': return out(selfHeal(pos[0]));
    default:
      process.stdout.write('context.mjs <config|crawl|resume|register|resolve|recent|self-heal> [path] [--flags]\n');
      process.exit(2);
  }
}
main();
