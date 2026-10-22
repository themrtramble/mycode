# MyCode - Open Source Multi-Agent AI Coding Assistant

An **OpenCode-style** CLI tool with full **multi-agent support**, **custom providers**, and **editable system prompts** — built in pure Python.

Built inspired by [sst/opencode](https://github.com/sst/opencode), but simpler, fully working, and focused on the multi-agent pipeline you asked for.

---

## 🎯 Features

### 1. Pre-built + Custom LLM Providers
- **8 pre-built providers**: Groq, Google Gemini, OpenRouter, DeepSeek, Cerebras, Together AI, Mistral, Ollama (local)
- **Add custom providers** with your own API URL, API key, and models
- **Delete custom providers** anytime
- **Switch active provider** on the fly
- **Set default model** per provider
- All providers use OpenAI-compatible API (works with most LLM gateways)

### 2. Normal Chat Mode
- Direct conversation with the AI
- Optional file tools (read/write/edit/list/run commands)
- Multi-turn conversation with history
- Slash commands: `/tools`, `/clear`, `/help`, `exit`

### 3. Multi-Agent Mode (The Killer Feature)
The complete pipeline you described:

```
User Task
    |
    v
[Planner] ----- enhances prompt + creates plan (3-6 steps)
    |
    v
[Worker] ----- executes the plan using file tools (writes actual code)
    |
    v
[Bug Analyzer] ----- reviews output, finds bugs
    |
    v
[Fixer] ----- fixes the bugs using file tools
    |
    +--- (loops back to Planner if bugs remain, max 3 rounds)
```

### 4. Editable System Prompts
- Each agent (Planner, Worker, Bug Analyzer, Fixer, Normal) has its own system prompt
- Edit any prompt interactively
- Append to existing prompt
- Reset to default anytime
- All saved in `~/.mycode/agents.json`

### 5. File Operation Tools (Agents Actually Write Code)
Agents can use these tools:
- `read_file(path)` — read a file
- `write_file(path, content)` — create or overwrite a file
- `edit_file(path, old_text, new_text)` — targeted edit
- `list_files(path)` — list directory contents
- `run_command(command)` — run shell commands (e.g. `python file.py` to test)

---

## 📦 Installation (Linux, macOS, Windows — All Supported)

MyCode can be installed via **Python (pip)** or **Node.js (npm)**. Both work on all operating systems.

### Option A: Python (pip) — Recommended

```bash
# 1. Clone the repo
git clone https://github.com/themrtramble/mycode.git
cd mycode

# 2. Run the universal installer (handles everything)
python install.py

# OR manual install:
pip install -e .

# 3. Use from anywhere
mycode
mycode chat "hello"
mycode agent "build a calculator"
```

**One-line install (after clone):**
```bash
cd mycode && python install.py
```

### Option B: Node.js (npm)

```bash
# Install globally via npm
npm install -g mycode-cli

# Or from source:
git clone https://github.com/themrtramble/mycode.git
cd mycode
npm install
npm link

# Use from anywhere
mycode
mycode chat "hello"
mycode agent "build a calculator"
```

### Option C: Direct run without install

```bash
# Python:
python -m mycode

# Node.js:
node bin/mycode.js
```

### Requirements

- **Python 3.9+** (for pip install) — check: `python --version`
- **Node.js 18+** (for npm install) — check: `node --version` (optional)
- **Internet connection** (for pip/npm install)
- **No GPU, no payment** — only free providers used

### What the installer does

Running `python install.py` will:
- ✅ Install the `openai` Python package
- ✅ Install the `mycode` package itself
- ✅ Create a `mycode` command in your PATH:
  - Linux/macOS: `~/.local/bin/mycode` (bash wrapper)
  - Windows: `%USERPROFILE%\.mycode\bin\mycode.bat` (batch wrapper)
- ✅ Update shell config (`.bashrc` / `.zshrc` on Unix, user PATH on Windows)
- ✅ Run a smoke test to verify everything works

**After install:**
- **Linux/macOS**: Run `source ~/.bashrc` (or open a new terminal)
- **Windows**: Close and reopen the terminal

Then from **ANY directory**, just type:

```bash
mycode
mycode chat "hello"
mycode agent "build a calculator"
```

---

## 🚀 Quick Start

### Step 1: Add your API key for a free provider

Get a free Groq API key from https://console.groq.com/keys (no credit card needed):

```bash
mycode provider add-key groq
# Paste your key when prompted
```

### Step 2: Set it as active provider

```bash
mycode provider use groq
```

### Step 3: Test the connection

```bash
mycode provider test groq
```

### Step 4: Try normal chat

```bash
mycode chat "what is recursion in Python?"
```

### Step 5: Try multi-agent mode (the magic)

```bash
mycode agent "build a simple Python calculator that can add, subtract, multiply, divide"
```

You'll see the full pipeline: Planner → Worker → Bug Analyzer → Fixer, with file tools being called live.

---

## 📚 Command Reference

### Provider Management

| Command | Description |
|---------|-------------|
| `mycode provider list` | Show all configured providers |
| `mycode provider add-key <id>` | Set API key for a provider |
| `mycode provider add` | Add a custom provider (interactive) |
| `mycode provider delete <id>` | Delete a custom provider |
| `mycode provider use <id>` | Set the active provider |
| `mycode provider model <id> <model>` | Set default model for provider |
| `mycode provider test <id>` | Test connection to a provider |

### Agent Prompts

| Command | Description |
|---------|-------------|
| `mycode prompts list` | List all configured agents |
| `mycode prompts show <id>` | Show an agent's system prompt |
| `mycode prompts edit [id]` | Edit an agent's prompt (interactive) |
| `mycode prompts reset` | Reset all prompts to defaults |

### Chat Modes

| Command | Description |
|---------|-------------|
| `mycode` | Open interactive menu |
| `mycode chat [prompt]` | Normal chat mode |
| `mycode agent [task]` | Multi-agent mode (Planner→Worker→Analyzer→Fixer) |
| `mycode agent "task" -r 5` | Multi-agent with custom round count |
| `mycode agent "task" -p groq` | Multi-agent with specific provider |

---

## 🛠 Adding a Custom Provider

```bash
$ mycode provider add

=== Add Custom Provider ===

Provider ID (e.g. 'myllm'): myllm
Display Name (e.g. 'My Custom LLM'): My Custom LLM
Base URL (OpenAI-compatible, e.g. https://api.example.com/v1): https://api.example.com/v1
API Key: sk-xxxxxxxxxxxxxxxxx
Models (comma-separated, e.g. model-a,model-b): model-large,model-small
Default model (default: model-large): model-large

✅ Custom provider 'myllm' added.

Set 'myllm' as active provider? (y/N): y
✅ Active provider set to 'myllm'.
```

Now you can use it:
```bash
mycode agent "do something" -p myllm
```

---

## ✏️ Editing Agent Prompts

```bash
$ mycode prompts edit planner

Editing: Planner
Description: Task ko chhote actionable steps mein todta hai
Recommended model: gemini-2.0-flash or llama-3.3-70b-versatile

Current system prompt:
------------------------------------------------------------
You are a senior software planner. Your job is to break down any task...

Options:
  1. Replace with new prompt (write in editor)
  2. Append to current prompt
  3. Reset to default
  4. Cancel

Choice (1-4): 1
```

---

## 🔧 Configuration Files

All config lives in `~/.mycode/`:

```
~/.mycode/
├── providers.json    # Providers + API keys
└── agents.json       # System prompts for each agent
```

You can edit these files directly with any text editor too.

---

## 💡 How Multi-Agent Mode Works (Step by Step)

When you run `mycode agent "build a calculator"`, here's exactly what happens:

1. **Planner** receives the prompt: "build a calculator"
   - Enhances it into a structured plan with 3-6 steps
   - Output: "Step 1: Create calc.py. Step 2: Add operations. Step 3: Add main loop..."

2. **Worker** receives the plan
   - Calls `write_file("calc.py", "...code...")` to create the file
   - Calls `run_command("python calc.py")` to test it
   - Returns summary of what it did

3. **Bug Analyzer** reviews Worker's output
   - Looks for syntax errors, logic bugs, missing imports
   - Returns either `NO_BUGS` or a list of specific bugs

4. If bugs found → **Fixer** is invoked
   - Uses `edit_file()` and `write_file()` to apply fixes
   - Returns summary of fixes

5. If `NO_BUGS` → ✅ Task complete!
   - Otherwise loops back to Planner (refined prompt) for round 2

---

## 🆓 Free Provider Setup (Zero Budget)

| Provider | Get Key | Free Limit |
|----------|---------|------------|
| **Groq** | https://console.groq.com/keys | 14,400 req/day |
| **Google Gemini** | https://aistudio.google.com/app/apikey | 1,500 req/day |
| **OpenRouter** | https://openrouter.ai/keys | 50 req/day (free models) |
| **Cerebras** | https://cloud.cerebras.ai | Free tier |
| **DeepSeek** | https://platform.deepseek.com | Free credits |
| **Ollama** (local) | https://ollama.com | Truly unlimited |

For unlimited free use, install Ollama locally and add it as a provider — no API key needed.

---

## 📁 Project Structure

```
mycode/
├── mycode/
│   ├── __init__.py       # Package metadata
│   ├── __main__.py       # Entry point (python -m mycode)
│   ├── cli.py           # CLI interface (argparse)
│   ├── config.py        # Config files + defaults
│   ├── providers.py     # LLM provider management
│   ├── agents.py        # Multi-agent orchestrator + normal chat
│   └── tools.py         # File operation tools for agents
├── requirements.txt
├── setup.py             # pip install -e .
└── README.md
```

---

## 🎨 Inspired By

- [sst/opencode](https://github.com/sst/opencode) — The original open-source AI coding agent
- [CrewAI](https://github.com/crewAIInc/crewAI) — Multi-agent framework
- [Aider](https://github.com/Aider-AI/aider) — AI pair programming

---

## 📝 License

MIT — Free to use, modify, distribute. Build your own "duniya ka sabse powerful AI" 💪

---

## 🚀 What's Next?

Once you have it running, you can:
- Add more specialized agents (Researcher, Translator, Tester)
- Build a web UI with Streamlit/Gradio
- Deploy to Hugging Face Spaces (free)
- Wrap it as a desktop app with Electron/Tauri
- Monetize as a SaaS product

The foundation is here — go build on top of it! 🚀
