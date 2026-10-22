#!/usr/bin/env node
/**
 * MyCode CLI - Node.js wrapper
 * ============================
 * Calls the Python mycode module under the hood.
 * This wrapper lets users install via `npm install -g .`
 * and use `mycode` from any terminal.
 *
 * Requirements:
 *   - Python 3.9+ must be installed
 *   - mycode Python package must be installed (pip install -e .)
 *
 * Usage:
 *   mycode                       # interactive menu
 *   mycode chat "hello"          # normal chat
 *   mycode agent "build X"       # multi-agent mode
 *   mycode provider list         # manage providers
 *   mycode prompts edit planner  # edit prompts
 */

const { spawn } = require("child_process");
const path = require("path");

// Detect python command (python3 preferred, fall back to python)
function findPython() {
  const candidates = process.platform === "win32"
    ? ["python", "python3", "py"]
    : ["python3", "python"];
  // We can't synchronously test which exists cleanly, so just return first
  // and let the spawn error out if not found.
  return candidates[0];
}

function main() {
  const python = findPython();
  const args = ["-m", "mycode", ...process.argv.slice(2)];

  const child = spawn(python, args, {
    stdio: "inherit",
    env: { ...process.env },
    cwd: process.cwd(),
  });

  child.on("error", (err) => {
    if (err.code === "ENOENT") {
      console.error("");
      console.error("✗ Python not found. Please install Python 3.9+:");
      console.error("  https://python.org/downloads");
      console.error("");
      console.error("Then install mycode Python package:");
      console.error("  pip install -e .");
      console.error("");
    } else {
      console.error("✗ Error launching mycode:", err.message);
    }
    process.exit(1);
  });

  child.on("exit", (code) => {
    process.exit(code || 0);
  });
}

main();
