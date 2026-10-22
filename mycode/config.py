"""
config.py - Configuration & file management for MyCode
========================================================
Handles:
  - User config directory (~/.mycode/)
  - providers.json (saved providers + API keys)
  - agents.json (system prompts for each agent)
  - Default providers and prompts
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List

# === Paths ===
HOME = Path.home()
CONFIG_DIR = HOME / ".mycode"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

PROVIDERS_FILE = CONFIG_DIR / "providers.json"
AGENTS_FILE = CONFIG_DIR / "agents.json"
HISTORY_FILE = CONFIG_DIR / "history.json"

# === Default Pre-built Providers (no API keys - user must add) ===
DEFAULT_PROVIDERS = {
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": "",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant",
                   "openai/gpt-oss-120b", "qwen/qwen3-32b"],
        "default_model": "llama-3.3-70b-versatile",
        "is_custom": False,
        "active": False
    },
    "gemini": {
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key": "",
        "models": ["gemini-2.0-flash", "gemini-2.5-flash",
                   "gemini-2.5-pro", "gemini-1.5-flash"],
        "default_model": "gemini-2.0-flash",
        "is_custom": False,
        "active": False
    },
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": "",
        "models": ["meta-llama/llama-3.3-70b-instruct:free",
                   "deepseek/deepseek-chat-v3-0324:free",
                   "qwen/qwen-2.5-72b-instruct:free",
                   "openai/gpt-oss-120b:free"],
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "is_custom": False,
        "active": False
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "default_model": "deepseek-chat",
        "is_custom": False,
        "active": False
    },
    "cerebras": {
        "name": "Cerebras",
        "base_url": "https://api.cerebras.ai/v1",
        "api_key": "",
        "models": ["llama-3.3-70b", "llama-3.1-8b"],
        "default_model": "llama-3.3-70b",
        "is_custom": False,
        "active": False
    },
    "together": {
        "name": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "api_key": "",
        "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo",
                   "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"],
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "is_custom": False,
        "active": False
    },
    "mistral": {
        "name": "Mistral",
        "base_url": "https://api.mistral.ai/v1",
        "api_key": "",
        "models": ["mistral-large-latest", "mistral-small-latest",
                   "open-mistral-7b", "open-mixtral-8x7b"],
        "default_model": "mistral-small-latest",
        "is_custom": False,
        "active": False
    },
    "ollama": {
        "name": "Ollama (Local)",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "models": ["llama3.2:3b", "llama3.2:1b", "qwen2.5:7b",
                   "deepseek-r1:7b", "codellama:7b"],
        "default_model": "llama3.2:3b",
        "is_custom": False,
        "active": False
    }
}

# === Default System Prompts for Each Agent ===
DEFAULT_AGENT_PROMPTS = {
    "planner": {
        "name": "Planner",
        "description": "Task ko chhote actionable steps mein todta hai",
        "system_prompt": (
            "You are a senior software planner. Your job is to break down any task "
            "into 3-6 clear, actionable, sequential steps. For each step, mention:\n"
            "1. What to do\n"
            "2. Which file to create/modify\n"
            "3. Expected output\n\n"
            "Respond in Hinglish (Hindi + English mix) if user writes in Hinglish. "
            "Be concise but complete. Output ONLY the plan as numbered steps."
        ),
        "model_hint": "gemini-2.0-flash or llama-3.3-70b-versatile"
    },
    "worker": {
        "name": "Worker",
        "description": "Plan ke steps ko execute karta hai - actual code likhta hai",
        "system_prompt": (
            "You are a skilled developer agent. You execute plans step-by-step. "
            "When asked to write code, ALWAYS use the file tools provided:\n"
            "- write_file(path, content) to create/overwrite files\n"
            "- read_file(path) to read existing files\n"
            "- list_files(dir) to see directory structure\n"
            "- edit_file(path, old, new) to modify files\n"
            "- run_command(command) to run shell commands\n\n"
            "Always write clean, working, well-commented code. "
            "Explain briefly what you did after each action. "
            "Respond in Hinglish if user writes in Hinglish."
        ),
        "model_hint": "llama-3.3-70b-versatile or deepseek-chat"
    },
    "bug_analyzer": {
        "name": "Bug Analyzer",
        "description": "Worker ke output/code ko check karta hai, bugs dhoondhta hai",
        "system_prompt": (
            "You are a strict code reviewer and bug analyzer. Examine the worker's "
            "output and code for:\n"
            "1. Syntax errors\n"
            "2. Logic bugs\n"
            "3. Missing imports\n"
            "4. Edge cases not handled\n"
            "5. Security issues\n\n"
            "If code is clean, respond 'NO_BUGS' followed by quality score /10.\n"
            "If bugs found, list each bug with: file, line, issue, suggested fix.\n"
            "Be thorough but not nitpicky. Respond in Hinglish."
        ),
        "model_hint": "deepseek-reasoner or llama-3.3-70b-versatile"
    },
    "fixer": {
        "name": "Fixer",
        "description": "Bug analyzer ke diye bugs fix karta hai",
        "system_prompt": (
            "You are a code fixer. The bug analyzer reported specific bugs. "
            "Your job is to fix each bug using file tools (edit_file, write_file). "
            "After fixing, summarize what you changed and why. "
            "If no bugs were reported, just confirm code is clean. "
            "Respond in Hinglish."
        ),
        "model_hint": "llama-3.3-70b-versatile"
    },
    "normal": {
        "name": "Normal Chat",
        "description": "Direct chat mode - koi agent loop nahi",
        "system_prompt": (
            "You are MyCode, a helpful AI coding assistant. "
            "You can answer questions, write code, explain concepts, debug issues. "
            "Be concise and helpful. Respond in the user's language. "
            "You can use file tools if asked to read/write code."
        ),
        "model_hint": "any"
    }
}


# === Loaders / Savers ===

def load_providers() -> Dict[str, Any]:
    """Load providers from config file. If not exists, create with defaults."""
    if PROVIDERS_FILE.exists():
        with open(PROVIDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    save_providers(DEFAULT_PROVIDERS)
    return DEFAULT_PROVIDERS.copy()


def save_providers(providers: Dict[str, Any]):
    """Save providers to config file."""
    with open(PROVIDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(providers, f, indent=2, ensure_ascii=False)


def load_agent_prompts() -> Dict[str, Any]:
    """Load agent system prompts. If not exists, create with defaults."""
    if AGENTS_FILE.exists():
        with open(AGENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    save_agent_prompts(DEFAULT_AGENT_PROMPTS)
    return DEFAULT_AGENT_PROMPTS.copy()


def save_agent_prompts(prompts: Dict[str, Any]):
    """Save agent prompts to config file."""
    with open(AGENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)


def get_active_provider() -> Dict[str, Any]:
    """Return the currently active provider. If none, return first with API key set."""
    providers = load_providers()
    for pid, p in providers.items():
        if p.get("active") and p.get("api_key"):
            return {"id": pid, **p}
    for pid, p in providers.items():
        if p.get("api_key"):
            p["active"] = True
            save_providers(providers)
            return {"id": pid, **p}
    return None


def set_active_provider(provider_id: str) -> bool:
    """Set a provider as active. Returns True if success."""
    providers = load_providers()
    if provider_id not in providers:
        return False
    for pid in providers:
        providers[pid]["active"] = (pid == provider_id)
    save_providers(providers)
    return True
