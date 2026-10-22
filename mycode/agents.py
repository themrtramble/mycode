"""
agents.py - Multi-Agent Orchestrator
=====================================
Implements the Planner -> Worker -> Bug Analyzer -> Fixer loop:

    User Task
        |
        v
   [Planner] -- prompt enhance --> plan
        |
        v
   [Worker] -- executes plan --> code/output
        |
        v
   [Bug Analyzer] -- reviews --> bug report
        |
        v
   [Fixer] -- fixes bugs --> final output
        |
        +--- (loop back to Planner if bugs remain, max 3 rounds)
"""

import json
from typing import Dict, Any, Optional, List

from .config import load_agent_prompts, save_agent_prompts, DEFAULT_AGENT_PROMPTS
from .providers import get_provider
from .tools import run_tool_loop, TOOL_DEFINITIONS


# ANSI colors (terminal)
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


def _print_header(text: str, color: str = C.CYAN):
    print(f"\n{color}{C.BOLD}{'=' * 70}{C.RESET}")
    print(f"{color}{C.BOLD}  {text}{C.RESET}")
    print(f"{color}{C.BOLD}{'=' * 70}{C.RESET}")


def _print_step(text: str, color: str = C.YELLOW):
    print(f"\n{color}{C.BOLD}>> {text}{C.RESET}")


def _print_agent(name: str, color: str):
    print(f"\n{color}{C.BOLD}[{name}]{C.RESET} ", end="")


# === Agent prompt getters ===

def get_agent_prompt(agent_id: str) -> str:
    prompts = load_agent_prompts()
    if agent_id not in prompts:
        return DEFAULT_AGENT_PROMPTS[agent_id]["system_prompt"]
    return prompts[agent_id]["system_prompt"]


def set_agent_prompt(agent_id: str, new_prompt: str) -> bool:
    prompts = load_agent_prompts()
    if agent_id not in prompts:
        return False
    prompts[agent_id]["system_prompt"] = new_prompt
    save_agent_prompts(prompts)
    return True


# === Multi-agent orchestration ===

def run_multi_agent(task: str, max_rounds: int = 3,
                    provider_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full multi-agent pipeline:
      Planner -> Worker -> Bug Analyzer -> Fixer
    Loops back to Planner if bugs remain (max_rounds times).
    """
    _print_header(f"MULTI-AGENT MODE STARTED | Task: {task[:60]}", C.MAGENTA)

    provider = get_provider(provider_id)
    if not provider:
        return {"error": "No provider available"}

    print(f"{C.DIM}Provider: {provider.name} | Model: {provider.model}{C.RESET}")

    planner_prompt = get_agent_prompt("planner")
    worker_prompt = get_agent_prompt("worker")
    analyzer_prompt = get_agent_prompt("bug_analyzer")
    fixer_prompt = get_agent_prompt("fixer")

    history = {
        "task": task,
        "provider": provider.name,
        "model": provider.model,
        "rounds": []
    }

    current_task = task

    for round_num in range(1, max_rounds + 1):
        _print_header(f"ROUND {round_num}/{max_rounds}", C.BLUE)

        round_data = {"round": round_num}

        # ============ STEP 1: PLANNER ============
        _print_step("STEP 1: PLANNER is enhancing prompt & making plan", C.CYAN)
        _print_agent("Planner", C.CYAN)
        print("thinking...")

        planner_user_msg = (
            f"User ka task: {current_task}\n\n"
            f"Is task ko 3-6 actionable steps mein todo. "
            f"Har step mein batao kya karna hai aur kis file mein."
        )
        plan = provider.chat_simple(
            system=planner_prompt,
            user=planner_user_msg,
            temperature=0.4,
            max_tokens=2048
        )
        round_data["plan"] = plan
        print(f"\n{C.CYAN}{C.BOLD}--- PLAN ---{C.RESET}")
        print(plan)
        print(f"{C.CYAN}{C.BOLD}------------{C.RESET}")

        # ============ STEP 2: WORKER ============
        _print_step("STEP 2: WORKER is executing the plan (with file tools)", C.YELLOW)
        _print_agent("Worker", C.YELLOW)
        print("working...")

        worker_messages = [
            {"role": "system", "content": worker_prompt},
            {"role": "user", "content": (
                f"Original task: {current_task}\n\n"
                f"Plan:\n{plan}\n\n"
                f"Ab plan ke hisaab se actual kaam karo. "
                f"File tools (write_file, read_file, edit_file, list_files, run_command) "
                f"use karke code likho aur execute karo. "
                f"Har step ke baad brief summary do."
            )}
        ]
        worker_output = run_tool_loop(provider, worker_messages, max_iterations=8)
        round_data["worker_output"] = worker_output
        print(f"\n{C.YELLOW}{C.BOLD}--- WORKER OUTPUT ---{C.RESET}")
        print(worker_output[:2000] + ("..." if len(worker_output) > 2000 else ""))
        print(f"{C.YELLOW}{C.BOLD}---------------------{C.RESET}")

        # ============ STEP 3: BUG ANALYZER ============
        _print_step("STEP 3: BUG ANALYZER is reviewing the output", C.RED)
        _print_agent("Bug Analyzer", C.RED)
        print("analyzing...")

        analyzer_user = (
            f"Original task: {current_task}\n\n"
            f"Plan:\n{plan[:1000]}\n\n"
            f"Worker ka output:\n{worker_output[:3000]}\n\n"
            f"Ab is output ko review karo. Bugs dhoondo ya 'NO_BUGS' bolo."
        )
        analysis = provider.chat_simple(
            system=analyzer_prompt,
            user=analyzer_user,
            temperature=0.3,
            max_tokens=2048
        )
        round_data["bug_analysis"] = analysis
        print(f"\n{C.RED}{C.BOLD}--- BUG ANALYSIS ---{C.RESET}")
        print(analysis)
        print(f"{C.RED}{C.BOLD}--------------------{C.RESET}")

        # ============ Check: are there bugs? ============
        no_bugs = "NO_BUGS" in analysis.upper() or "no bugs" in analysis.lower()

        if no_bugs:
            _print_step("NO BUGS FOUND! Task complete.", C.GREEN)
            round_data["status"] = "completed_clean"
            history["rounds"].append(round_data)
            history["final_output"] = worker_output
            history["status"] = "completed_clean"
            break

        # ============ STEP 4: FIXER ============
        _print_step("STEP 4: FIXER is fixing the bugs", C.MAGENTA)
        _print_agent("Fixer", C.MAGENTA)
        print("fixing...")

        fixer_messages = [
            {"role": "system", "content": fixer_prompt},
            {"role": "user", "content": (
                f"Original task: {current_task}\n\n"
                f"Bug Analyzer ne yeh bugs report kiye:\n{analysis}\n\n"
                f"Ab har bug ko fix karo. File tools use karke edit_file/write_file "
                f"se fixes lagao. Phir summary do kya fix kiya."
            )}
        ]
        fixer_output = run_tool_loop(provider, fixer_messages, max_iterations=8)
        round_data["fixer_output"] = fixer_output
        print(f"\n{C.MAGENTA}{C.BOLD}--- FIXER OUTPUT ---{C.RESET}")
        print(fixer_output[:2000] + ("..." if len(fixer_output) > 2000 else ""))
        print(f"{C.MAGENTA}{C.BOLD}--------------------{C.RESET}")

        round_data["status"] = "fixed_bugs"
        history["rounds"].append(round_data)

        # Update task for next round (refined)
        current_task = (
            f"{task}\n\n"
            f"(Previous round me yeh bugs the: {analysis[:500]}. "
            f"Inhe fix kiya gaya. Ab verify karo sab sahi hai.)"
        )
    else:
        # Loop exhausted without clean completion
        _print_step(f"Max rounds ({max_rounds}) reached. Task may need manual review.", C.YELLOW)
        history["status"] = "max_rounds_reached"
        history["final_output"] = fixer_output if 'fixer_output' in locals() else worker_output

    _print_header("MULTI-AGENT PIPELINE COMPLETE", C.GREEN)
    print(f"{C.GREEN}Status: {history.get('status', 'unknown')}{C.RESET}")
    print(f"{C.GREEN}Total rounds: {len(history['rounds'])}{C.RESET}")
    print(f"{C.GREEN}Provider: {provider.name} | Model: {provider.model}{C.RESET}")

    return history


# === Normal chat mode (direct conversation) ===

def run_normal_chat(initial_prompt: Optional[str] = None,
                    provider_id: Optional[str] = None):
    """
    Interactive normal chat mode.
    User talks directly to LLM with optional file tools.
    """
    _print_header("NORMAL CHAT MODE | Type 'exit' to quit, '/tools' to toggle", C.CYAN)

    provider = get_provider(provider_id)
    if not provider:
        return

    system_prompt = get_agent_prompt("normal")
    print(f"{C.DIM}Provider: {provider.name} | Model: {provider.model}{C.RESET}")
    print(f"{C.DIM}System prompt: {system_prompt[:100]}...{C.RESET}\n")

    messages = [{"role": "system", "content": system_prompt}]
    use_tools = True

    if initial_prompt:
        print(f"{C.CYAN}You: {initial_prompt}{C.RESET}")
        messages.append({"role": "user", "content": initial_prompt})
        _process_message(provider, messages, use_tools)

    while True:
        try:
            user_input = input(f"\n{C.CYAN}{C.BOLD}You: {C.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{C.YELLOW}Goodbye!{C.RESET}")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "/exit", "/quit"):
            print(f"\n{C.YELLOW}Goodbye!{C.RESET}")
            break
        if user_input.lower() in ("/tools", "/tool"):
            use_tools = not use_tools
            print(f"{C.DIM}Tools {'enabled' if use_tools else 'disabled'}{C.RESET}")
            continue
        if user_input.lower() in ("/clear", "/reset"):
            messages = [{"role": "system", "content": system_prompt}]
            print(f"{C.DIM}Conversation cleared.{C.RESET}")
            continue
        if user_input.lower() in ("/help", "/?"):
            _print_help()
            continue

        messages.append({"role": "user", "content": user_input})
        _process_message(provider, messages, use_tools)


def _process_message(provider, messages, use_tools):
    """Process a single message exchange."""
    print(f"{C.GREEN}{C.BOLD}AI: {C.RESET}", end="")
    try:
        if use_tools:
            response = run_tool_loop(provider, messages, max_iterations=6)
            print(response)
        else:
            response = provider.chat(messages, temperature=0.7, max_tokens=2048)
            content = response.content or "(no response)"
            print(content)
            messages.append({"role": "assistant", "content": content})
    except Exception as e:
        print(f"{C.RED}Error: {e}{C.RESET}")


def _print_help():
    print(f"""
{C.BOLD}Commands:{C.RESET}
  /tools   - Toggle file tools on/off (currently affects next message)
  /clear   - Clear conversation history
  /help    - Show this help
  exit     - Quit MyCode

{C.BOLD}Normal chat mode:{C.RESET}
  Direct conversation with the AI. Can read/write files if tools enabled.
""")


# === Agent prompt editor ===

def edit_agent_prompt(agent_id: Optional[str] = None):
    """Interactive editor for agent system prompts."""
    prompts = load_agent_prompts()

    if agent_id is None:
        print(f"\n{C.BOLD}Available agents:{C.RESET}")
        for aid, info in prompts.items():
            print(f"  {aid:<15} - {info['name']} ({info['description']})")
        agent_id = input(f"\n{C.CYAN}Agent ID to edit: {C.RESET}").strip()
        if agent_id not in prompts:
            print(f"{C.RED}Invalid agent ID.{C.RESET}")
            return

    info = prompts[agent_id]
    print(f"\n{C.BOLD}Editing: {info['name']}{C.RESET}")
    print(f"{C.DIM}Description: {info['description']}{C.RESET}")
    print(f"{C.DIM}Recommended model: {info['model_hint']}{C.RESET}")
    print(f"\n{C.BOLD}Current system prompt:{C.RESET}")
    print(f"{C.DIM}{'-' * 60}{C.RESET}")
    print(info["system_prompt"])
    print(f"{C.DIM}{'-' * 60}{C.RESET}")

    print(f"\n{C.YELLOW}Options:{C.RESET}")
    print(f"  1. Replace with new prompt (write in editor)")
    print(f"  2. Append to current prompt")
    print(f"  3. Reset to default")
    print(f"  4. Cancel")

    choice = input(f"\n{C.CYAN}Choice (1-4): {C.RESET}").strip()

    if choice == "1":
        print(f"\n{C.BOLD}Enter new prompt (Ctrl+D or empty line + Enter to finish):{C.RESET}")
        lines = []
        try:
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    lines.pop()  # remove last empty
                    break
                lines.append(line)
        except EOFError:
            pass
        new_prompt = "\n".join(lines)
        if new_prompt.strip():
            set_agent_prompt(agent_id, new_prompt)
            print(f"{C.GREEN}✓ Prompt updated for '{agent_id}'{C.RESET}")
        else:
            print(f"{C.YELLOW}Empty prompt, no change.{C.RESET}")
    elif choice == "2":
        addition = input(f"{C.CYAN}Text to append: {C.RESET}")
        new_prompt = info["system_prompt"] + "\n\n" + addition
        set_agent_prompt(agent_id, new_prompt)
        print(f"{C.GREEN}✓ Prompt appended for '{agent_id}'{C.RESET}")
    elif choice == "3":
        if agent_id in DEFAULT_AGENT_PROMPTS:
            set_agent_prompt(agent_id, DEFAULT_AGENT_PROMPTS[agent_id]["system_prompt"])
            print(f"{C.GREEN}✓ Reset to default for '{agent_id}'{C.RESET}")
        else:
            print(f"{C.RED}No default for custom agent.{C.RESET}")
    else:
        print(f"{C.YELLOW}Cancelled.{C.RESET}")


def list_agents():
    """Print all configured agents."""
    prompts = load_agent_prompts()
    print(f"\n{C.BOLD}Configured Agents:{C.RESET}\n")
    print(f"{'ID':<15}{'Name':<18}{'Description'}")
    print("-" * 70)
    for aid, info in prompts.items():
        print(f"{aid:<15}{info['name']:<18}{info['description']}")
    print()


def show_agent_prompt(agent_id: str):
    """Show one agent's full system prompt."""
    prompts = load_agent_prompts()
    if agent_id not in prompts:
        print(f"{C.RED}Agent '{agent_id}' not found.{C.RESET}")
        return
    info = prompts[agent_id]
    print(f"\n{C.BOLD}Agent: {info['name']} ({agent_id}){C.RESET}")
    print(f"{C.DIM}Description: {info['description']}{C.RESET}")
    print(f"{C.DIM}Recommended model: {info['model_hint']}{C.RESET}")
    print(f"\n{C.BOLD}System Prompt:{C.RESET}")
    print(f"{C.DIM}{'=' * 70}{C.RESET}")
    print(info["system_prompt"])
    print(f"{C.DIM}{'=' * 70}{C.RESET}\n")
