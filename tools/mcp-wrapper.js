#!/usr/bin/env node

// mcp-wrapper.js — Ensures MCP server processes are cleaned up when Claude Code exits.
//
// Problem: Claude Code does not reliably kill MCP server child processes on exit.
// Docker containers survive because they run under Docker Daemon, not as direct children.
// npx/native processes become orphans (PPID=1) on macOS. This affects all platforms.
// See: https://github.com/anthropics/claude-code/issues/1935
//      https://github.com/anthropics/claude-code/issues/29058
//
// Solution: This wrapper sits between Claude Code and the MCP server.
// It monitors stdin — when Claude Code dies (any way: exit, crash, terminal close,
// SIGKILL), the OS closes the pipe. Wrapper receives EOF/SIGHUP and kills the child.
//
// Usage in ~/.claude.json:
//   Before:  "command": "docker", "args": ["run", "-i", "--rm", ...]
//   After:   "command": "node",   "args": ["/path/to/mcp-wrapper.js", "docker", "run", "-i", "--rm", ...]
//
//   Before:  "command": "npx",    "args": ["-y", "@upstash/context7-mcp@latest"]
//   After:   "command": "node",   "args": ["/path/to/mcp-wrapper.js", "npx", "-y", "@upstash/context7-mcp@latest"]
//
// Environment variables:
//   MCP_WRAPPER_DEBUG=1  — enable debug logging to ~/mcp-wrapper.log
//
// Cross-platform: macOS, Linux, Windows (Node.js + child_process)

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// --- Config ---
const DEBUG = process.env.MCP_WRAPPER_DEBUG === '1';
const LOG_FILE = path.join(os.homedir(), 'mcp-wrapper.log');
const KILL_TIMEOUT_MS = 3000;
const EXIT_DELAY_MS = 1000;

// --- Logging ---
function log(msg) {
  if (!DEBUG) return;
  const ts = new Date().toISOString();
  try { fs.appendFileSync(LOG_FILE, `${ts} | ${msg}\n`); } catch {}
}

// --- Parse arguments ---
const childArgs = process.argv.slice(2);
if (childArgs.length === 0) {
  process.stderr.write('mcp-wrapper: no command specified\n');
  process.exit(1);
}

// --- Detect Docker ---
const isDocker = childArgs[0] === 'docker' &&
  (childArgs.includes('run') || childArgs.includes('create'));

// For Docker: inject --name so we can force-remove by name on cleanup
let dockerContainerName = null;
const finalArgs = [...childArgs];
if (isDocker) {
  const runIdx = finalArgs.indexOf('run');
  if (runIdx !== -1) {
    dockerContainerName = `mcp-wrapped-${process.pid}-${Date.now()}`;
    finalArgs.splice(runIdx + 1, 0, '--name', dockerContainerName);
  }
}

log(`STARTED (pid=${process.pid}, ppid=${process.ppid})`);
log(`command: ${finalArgs.join(' ')}`);
if (dockerContainerName) log(`docker name: ${dockerContainerName}`);

// --- Spawn child ---
const child = spawn(finalArgs[0], finalArgs.slice(1), {
  stdio: ['pipe', 'pipe', 'inherit'],
  windowsHide: true,
});
log(`child spawned (pid=${child.pid})`);

// --- Forward stdin/stdout ---
process.stdin.on('data', (chunk) => {
  if (!child.killed) child.stdin.write(chunk);
});
child.stdout.on('data', (chunk) => {
  process.stdout.write(chunk);
});
child.stdout.on('error', () => {}); // ignore broken pipe

// --- Cleanup ---
let cleanupDone = false;

function cleanup(reason) {
  if (cleanupDone) return;
  cleanupDone = true;
  log(`cleanup: ${reason}`);

  if (isDocker && dockerContainerName) {
    try {
      execSync(`docker rm -f ${dockerContainerName}`, { timeout: 5000, stdio: 'ignore' });
      log('docker container removed');
    } catch (e) {
      log(`docker rm failed: ${e.message}`);
    }
  } else if (child.pid && !child.killed) {
    log(`killing child pid=${child.pid}`);
    child.kill('SIGTERM');
    setTimeout(() => {
      if (!child.killed) {
        try { child.kill('SIGKILL'); } catch {}
        log('sent SIGKILL');
      }
    }, KILL_TIMEOUT_MS);
  }
}

function cleanupAndExit(reason, code = 0) {
  cleanup(reason);
  setTimeout(() => process.exit(code), EXIT_DELAY_MS);
}

// --- Lifecycle events ---

// KEY: when Claude Code dies, stdin pipe breaks → EOF or SIGHUP
process.stdin.on('end', () => { log('stdin END'); cleanupAndExit('stdin-end'); });
process.stdin.on('error', (err) => { log(`stdin ERROR: ${err.message}`); cleanupAndExit('stdin-error', 1); });

// Terminal close sends SIGHUP (verified experimentally)
process.on('SIGHUP', () => { log('SIGHUP'); cleanupAndExit('SIGHUP'); });
process.on('SIGTERM', () => { log('SIGTERM'); cleanupAndExit('SIGTERM'); });
process.on('SIGINT', () => { log('SIGINT'); cleanupAndExit('SIGINT'); });

// When child exits naturally, we exit too
child.on('exit', (code, signal) => {
  log(`child exited (code=${code}, signal=${signal})`);
  process.exit(code ?? 1);
});

child.on('error', (err) => {
  log(`child error: ${err.message}`);
  process.exit(1);
});

// Keep stdin reading
process.stdin.resume();
