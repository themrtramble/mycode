"""
tools.py - File operation tools that AI agents can use
========================================================
Agents can call these to actually read/write/edit code.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass


WORKSPACE_DIR = Path.cwd().resolve()


def _safe_path(path: str) -> Path:
    """Resolve path safely."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (WORKSPACE_DIR / p).resolve()
    else:
        p = p.resolve()
    return p


@dataclass
class ToolResult:
    success: bool
    output: str
    data: Any = None


# === Tool definitions (OpenAI function-calling format) ===
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a file. Returns the file content as text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with the given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to write."},
                    "content": {"type": "string", "description": "Full content to write to the file."}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace a specific string in a file with a new string. Use for targeted edits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."},
                    "old_text": {"type": "string", "description": "Exact text to find (must match exactly)."},
                    "new_text": {"type": "string", "description": "Text to replace it with."}
                },
                "required": ["path", "old_text", "new_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories in a given directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path. Use '.' for current.", "default": "."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command (like running tests, ls, python file.py). Use carefully.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute."}
                },
                "required": ["command"]
            }
        }
    }
]


def execute_tool(name: str, args: Dict[str, Any]) -> ToolResult:
    """Execute a single tool call."""
    try:
        if name == "read_file":
            return _read_file(args["path"])
        elif name == "write_file":
            return _write_file(args["path"], args["content"])
        elif name == "edit_file":
            return _edit_file(args["path"], args["old_text"], args["new_text"])
        elif name == "list_files":
            return _list_files(args["path"])
        elif name == "run_command":
            return _run_command(args["command"])
        else:
            return ToolResult(False, f"Unknown tool: {name}")
    except Exception as e:
        return ToolResult(False, f"Error in {name}: {e}")


def _read_file(path: str) -> ToolResult:
    p = _safe_path(path)
    if not p.exists():
        return ToolResult(False, f"File not found: {p}")
    if not p.is_file():
        return ToolResult(False, f"Not a file: {p}")
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        return ToolResult(True, content, {"path": str(p), "lines": len(content.splitlines())})
    except Exception as e:
        return ToolResult(False, f"Read error: {e}")


def _write_file(path: str, content: str) -> ToolResult:
    p = _safe_path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return ToolResult(True, f"File written: {p} ({len(content)} chars)", {"path": str(p)})
    except Exception as e:
        return ToolResult(False, f"Write error: {e}")


def _edit_file(path: str, old_text: str, new_text: str) -> ToolResult:
    p = _safe_path(path)
    if not p.exists():
        return ToolResult(False, f"File not found: {p}")
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        if old_text not in content:
            return ToolResult(False, f"Text not found in file: {old_text[:80]}...")
        count = content.count(old_text)
        new_content = content.replace(old_text, new_text)
        p.write_text(new_content, encoding="utf-8")
        return ToolResult(
            True,
            f"Edited {p} - {count} occurrence(s) replaced",
            {"path": str(p), "replacements": count}
        )
    except Exception as e:
        return ToolResult(False, f"Edit error: {e}")


def _list_files(path: str) -> ToolResult:
    p = _safe_path(path)
    if not p.exists():
        return ToolResult(False, f"Directory not found: {p}")
    if not p.is_dir():
        return ToolResult(False, f"Not a directory: {p}")
    try:
        items = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
        items = [i for i in items if not i.name.startswith('.') and i.name != '__pycache__']
        lines = []
        for item in items:
            tag = "[DIR] " if item.is_dir() else "[FILE]"
            try:
                size = item.stat().st_size if item.is_file() else 0
                size_str = f" ({_human_size(size)})" if size else ""
            except Exception:
                size_str = ""
            lines.append(f"{tag} {item.name}{size_str}")
        return ToolResult(True, "\n".join(lines) if lines else "(empty)", {"path": str(p)})
    except Exception as e:
        return ToolResult(False, f"List error: {e}")


def _run_command(command: str) -> ToolResult:
    """Run shell command with timeout."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30,
            cwd=str(WORKSPACE_DIR)
        )
        output = result.stdout
        if result.stderr:
            output += f"\n--- STDERR ---\n{result.stderr}"
        output += f"\n--- EXIT CODE: {result.returncode} ---"
        return ToolResult(result.returncode == 0, output, {"exit_code": result.returncode})
    except subprocess.TimeoutExpired:
        return ToolResult(False, "Command timed out (30s limit)")
    except Exception as e:
        return ToolResult(False, f"Command error: {e}")


def _human_size(num: int) -> str:
    """Convert bytes to human readable."""
    for unit in ["B", "K", "M", "G"]:
        if abs(num) < 1024:
            return f"{num:.0f}{unit}"
        num /= 1024
    return f"{num:.1f}T"


def run_tool_loop(provider, messages: List[Dict], max_iterations: int = 10) -> str:
    """
    Run a tool-calling loop with the LLM until it produces a final answer
    or hits max_iterations. Returns the final text response.
    """
    for iteration in range(max_iterations):
        response = provider.chat(
            messages,
            tools=TOOL_DEFINITIONS,
            temperature=0.4,
            max_tokens=4096
        )

        # If no tool calls, return content
        tool_calls = getattr(response, "tool_calls", None)
        if not tool_calls:
            return response.content or "(no response)"

        # Append assistant message with tool_calls
        messages.append({
            "role": "assistant",
            "content": response.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in tool_calls
            ]
        })

        # Execute each tool call
        for tc in tool_calls:
            try:
                args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) \
                    else tc.function.arguments
            except Exception:
                args = {}

            print(f"  [TOOL] {tc.function.name}({json.dumps(args, ensure_ascii=False)[:100]})")
            result = execute_tool(tc.function.name, args)
            status = "OK" if result.success else "FAIL"
            print(f"         -> {status}: {result.output[:120]}")

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result.output[:4000]
            })

    return "(max tool iterations reached)"
