#!/usr/bin/env python3
"""
MyCode CLI - Main entry point
==============================
Usage:
    mycode                      - Interactive menu
    mycode chat [prompt]        - Normal chat mode
    mycode agent [task]         - Multi-agent mode
    mycode provider list        - Show all providers
    mycode provider add-key <id> - Set API key for a provider
    mycode provider add          - Add custom provider (interactive)
    mycode provider delete <id>  - Delete custom provider
    mycode provider use <id>     - Set active provider
    mycode provider model <id> <model> - Set default model
    mycode prompts list         - List all agents
    mycode prompts show <id>    - Show agent's prompt
    mycode prompts edit [id]    - Edit agent's prompt
    mycode --version            - Show version
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent dir to path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from mycode import __version__
from mycode.config import load_providers, load_agent_prompts
from mycode.providers import (
    list_providers, get_provider, set_api_key, add_custom_provider,
    delete_custom_provider, set_default_model, set_active_provider
)
from mycode.agents import (
    run_normal_chat, run_multi_agent, edit_agent_prompt,
    list_agents, show_agent_prompt
)


def cmd_provider(args):
    """Handle provider subcommands."""
    if args.subcommand == "list":
        list_providers()

    elif args.subcommand == "add-key":
        if not args.value:
            print("Enter API key (input hidden):")
            import getpass
            key = getpass.getpass("API Key: ").strip()
        else:
            key = args.value
        if not key:
            print("❌ Empty API key.")
            return
        set_api_key(args.provider_id, key)

    elif args.subcommand == "add":
        print("\n=== Add Custom Provider ===\n")
        pid = input("Provider ID (e.g. 'myllm'): ").strip()
        if not pid:
            print("❌ ID required.")
            return
        name = input("Display Name (e.g. 'My Custom LLM'): ").strip() or pid
        base_url = input("Base URL (OpenAI-compatible, e.g. https://api.example.com/v1): ").strip()
        if not base_url:
            print("❌ Base URL required.")
            return
        api_key = input("API Key: ").strip()
        models_str = input("Models (comma-separated, e.g. model-a,model-b): ").strip()
        models = [m.strip() for m in models_str.split(",") if m.strip()]
        if not models:
            print("❌ At least one model required.")
            return
        default_model = input(f"Default model (default: {models[0]}): ").strip() or models[0]
        add_custom_provider(pid, name, base_url, api_key, models, default_model)
        use_now = input(f"\nSet '{pid}' as active provider? (y/N): ").strip().lower()
        if use_now == 'y':
            set_active_provider(pid)

    elif args.subcommand == "delete":
        if not args.provider_id:
            print("❌ Provider ID required. Usage: mycode provider delete <id>")
            return
        delete_custom_provider(args.provider_id)

    elif args.subcommand == "use":
        if not args.provider_id:
            print("❌ Provider ID required. Usage: mycode provider use <id>")
            return
        if set_active_provider(args.provider_id):
            print(f"✅ Active provider set to '{args.provider_id}'.")

    elif args.subcommand == "model":
        if not args.provider_id or not args.value:
            print("❌ Usage: mycode provider model <provider_id> <model_name>")
            return
        set_default_model(args.provider_id, args.value)

    elif args.subcommand == "test":
        if not args.provider_id:
            print("❌ Provider ID required. Usage: mycode provider test <id>")
            return
        print(f"\nTesting provider '{args.provider_id}'...")
        p = get_provider(args.provider_id)
        if p:
            print(f"Provider: {p.name}")
            print(f"Base URL: {p.base_url}")
            print(f"Model: {p.model}")
            print("Sending test message...")
            try:
                resp = p.chat_simple(
                    system="You are a test assistant. Reply briefly.",
                    user="Say 'hello from <your model name>' in one short sentence.",
                    max_tokens=100
                )
                print(f"\n✅ Response:\n{resp}")
            except Exception as e:
                print(f"\n❌ Error: {e}")

    else:
        print("Unknown provider command. Use: list, add-key, add, delete, use, model, test")


def cmd_prompts(args):
    """Handle prompts subcommands."""
    if args.subcommand == "list":
        list_agents()
    elif args.subcommand == "show":
        if not args.agent_id:
            print("❌ Agent ID required. Usage: mycode prompts show <id>")
            return
        show_agent_prompt(args.agent_id)
    elif args.subcommand == "edit":
        edit_agent_prompt(args.agent_id)
    elif args.subcommand == "reset":
        from mycode.config import DEFAULT_AGENT_PROMPTS, save_agent_prompts
        save_agent_prompts(DEFAULT_AGENT_PROMPTS.copy())
        print("✅ All agent prompts reset to defaults.")
    else:
        print("Unknown prompts command. Use: list, show, edit, reset")


def cmd_chat(args):
    """Run normal chat mode."""
    run_normal_chat(initial_prompt=args.prompt)


def cmd_agent(args):
    """Run multi-agent mode."""
    if not args.task:
        print(f"\n{'=' * 60}")
        print("  MULTI-AGENT MODE")
        print(f"{'=' * 60}")
        args.task = input("📝 Enter your task: ").strip()
        if not args.task:
            print("❌ No task provided.")
            return

    rounds = args.rounds if args.rounds else 3
    run_multi_agent(args.task, max_rounds=rounds, provider_id=args.provider)


def interactive_menu():
    """Show interactive menu when no command given."""
    from mycode.config import get_active_provider

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   MyCode v{__version__}  -  Multi-Agent AI Coding Assistant     ║
║   OpenCode-style clone with multi-agent + custom providers    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

    active = get_active_provider()
    if active:
        print(f"  Active provider: {active.get('name', active['id'])} ({active['id']})")
        print(f"  Default model:   {active.get('default_model', '?')}")
    else:
        print("  ⚠️  No provider configured yet!")
        print("  Run: mycode provider list     # see available providers")
        print("  Run: mycode provider add-key groq    # add your API key")

    print(f"""
  {__import__('mycode').C if hasattr(__import__('mycode'), 'C') else ''}
  Quick start:
    1. Chat        - Normal conversation with AI
    2. Agent       - Multi-agent mode (Planner -> Worker -> Bug Analyzer -> Fixer)
    3. Providers   - Manage LLM providers
    4. Prompts     - Edit system prompts for each agent
    5. Exit

  Or use CLI directly:
    mycode chat "explain Python decorators"
    mycode agent "build a simple calculator in Python"
""")

    while True:
        try:
            choice = input("Choose (1-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return

        if choice == "1":
            run_normal_chat()
            break
        elif choice == "2":
            task = input("\n📝 Enter task for multi-agent: ").strip()
            if task:
                run_multi_agent(task)
            break
        elif choice == "3":
            list_providers()
        elif choice == "4":
            edit_agent_prompt()
        elif choice == "5":
            print("Goodbye!")
            return
        else:
            print("Invalid choice. Enter 1-5.")


def main():
    parser = argparse.ArgumentParser(
        prog="mycode",
        description="MyCode - Multi-Agent AI Coding Assistant (OpenCode-style clone)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--version", action="version", version=f"mycode {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # chat
    chat_parser = subparsers.add_parser("chat", help="Normal chat mode")
    chat_parser.add_argument("prompt", nargs="?", help="Initial prompt (optional)")

    # agent
    agent_parser = subparsers.add_parser("agent", help="Multi-agent mode")
    agent_parser.add_argument("task", nargs="?", help="Task to run")
    agent_parser.add_argument("-r", "--rounds", type=int, default=3, help="Max rounds")
    agent_parser.add_argument("-p", "--provider", help="Provider ID to use")

    # provider
    prov_parser = subparsers.add_parser("provider", help="Manage LLM providers")
    prov_sub = prov_parser.add_subparsers(dest="subcommand", required=True)
    prov_sub.add_parser("list", help="List all providers")
    ak = prov_sub.add_parser("add-key", help="Set API key for a provider")
    ak.add_argument("provider_id")
    ak.add_argument("value", nargs="?", help="API key (will prompt if not provided)")
    add = prov_sub.add_parser("add", help="Add a custom provider")
    add.add_argument("provider_id", nargs="?")  # for compatibility
    dele = prov_sub.add_parser("delete", help="Delete a custom provider")
    dele.add_argument("provider_id")
    use = prov_sub.add_parser("use", help="Set active provider")
    use.add_argument("provider_id")
    model = prov_sub.add_parser("model", help="Set default model")
    model.add_argument("provider_id")
    model.add_argument("value")
    test = prov_sub.add_parser("test", help="Test a provider connection")
    test.add_argument("provider_id")

    # prompts
    prompts_parser = subparsers.add_parser("prompts", help="Manage agent system prompts")
    prompts_sub = prompts_parser.add_subparsers(dest="subcommand", required=True)
    prompts_sub.add_parser("list", help="List all agents")
    show = prompts_sub.add_parser("show", help="Show an agent's prompt")
    show.add_argument("agent_id")
    edit = prompts_sub.add_parser("edit", help="Edit an agent's prompt")
    edit.add_argument("agent_id", nargs="?")
    prompts_sub.add_parser("reset", help="Reset all prompts to defaults")

    args = parser.parse_args()

    if args.command is None:
        interactive_menu()
    elif args.command == "chat":
        cmd_chat(args)
    elif args.command == "agent":
        cmd_agent(args)
    elif args.command == "provider":
        cmd_provider(args)
    elif args.command == "prompts":
        cmd_prompts(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
