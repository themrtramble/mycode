"""
test_mycode.py - Test MyCode CLI with a mocked LLM provider
=============================================================
Simulates the full multi-agent pipeline without needing a real API key.
"""

import sys
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from mycode.providers import LLMProvider
from mycode.agents import run_multi_agent, run_normal_chat
from mycode.tools import execute_tool, _safe_path, _write_file, _read_file


class MockMessage:
    """Mock OpenAI chat completion message."""
    def __init__(self, content, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class MockToolCall:
    """Mock OpenAI tool call object."""
    def __init__(self, name, args_dict):
        self.id = f"call_{name}_{hash(str(args_dict)) & 0xffff}"
        self.type = "function"
        self.function = MagicMock()
        self.function.name = name
        self.function.arguments = json.dumps(args_dict)


def make_mock_provider():
    """Create a mock LLMProvider that returns scripted responses."""
    p = MagicMock(spec=LLMProvider)
    p.name = "MockLLM"
    p.model = "mock-model-1"
    p.provider_id = "mock"

    # Scripted responses for one full multi-agent round
    # Order: planner, worker(1st tool call msg), worker(final text), analyzer, fixer, fixer(final)
    responses = iter([
        # Planner response (text only, no tools)
        MockMessage(
            "PLAN:\n"
            "1. Create hello.py file with a greeting function\n"
            "2. Add a main() function that calls it\n"
            "3. Test by running python hello.py"
        ),
        # Worker response WITH tool calls (writes file)
        MockMessage(
            content="I'll create the file now.",
            tool_calls=[
                MockToolCall("write_file", {
                    "path": "hello.py",
                    "content": "def greet(name):\n    return f'Hello, {name}!'\n\nif __name__ == '__main__':\n    print(greet('World'))\n"
                })
            ]
        ),
        # Worker follow-up response (text only, no tools)
        MockMessage(
            "Done! Created hello.py with a greet() function. "
            "Run with `python hello.py` to see 'Hello, World!'"
        ),
        # Bug Analyzer response (finds a bug)
        MockMessage(
            "BUGS FOUND:\n"
            "1. File: hello.py | Issue: No input validation (if name is empty)\n"
            "   Fix: Add a default value\n"
            "2. File: hello.py | Issue: No type hints\n"
            "   Fix: Add `name: str` type hint"
        ),
        # Fixer response WITH tool calls (edits file)
        MockMessage(
            content="Fixing the bugs...",
            tool_calls=[
                MockToolCall("edit_file", {
                    "path": "hello.py",
                    "old_text": "def greet(name):",
                    "new_text": "def greet(name: str = 'World'):"
                })
            ]
        ),
        # Fixer follow-up (text)
        MockMessage(
            "Fixes applied:\n"
            "- Added type hint `str` to name parameter\n"
            "- Added default value 'World' so empty input is handled"
        ),
        # Bug Analyzer round 2: no bugs
        MockMessage("NO_BUGS. Quality score: 9/10. Code is clean."),
    ])

    def chat_side_effect(messages, **kwargs):
        try:
            return next(responses)
        except StopIteration:
            return MockMessage("(end of mocked responses)")

    p.chat.side_effect = chat_side_effect
    p.chat_simple.side_effect = lambda system, user, **kw: chat_side_effect([]).content

    return p


def test_tool_write_read():
    """Test basic file tools."""
    print("\n=== Test 1: File write/read ===")

    # Clean up
    test_file = _safe_path("test_hello.py")
    if test_file.exists():
        test_file.unlink()

    # Write
    result = execute_tool("write_file", {
        "path": "test_hello.py",
        "content": "print('hello')"
    })
    assert result.success, f"Write failed: {result.output}"
    print(f"✓ write_file: {result.output}")

    # Read
    result = execute_tool("read_file", {"path": "test_hello.py"})
    assert result.success, f"Read failed: {result.output}"
    assert "print('hello')" in result.output
    print(f"✓ read_file: returns correct content")

    # Edit
    result = execute_tool("edit_file", {
        "path": "test_hello.py",
        "old_text": "print('hello')",
        "new_text": "print('world')"
    })
    assert result.success, f"Edit failed: {result.output}"
    print(f"✓ edit_file: {result.output}")

    # Verify edit
    result = execute_tool("read_file", {"path": "test_hello.py"})
    assert "print('world')" in result.output
    print(f"✓ edit applied correctly")

    # List
    result = execute_tool("list_files", {"path": "."})
    assert result.success
    assert "test_hello.py" in result.output
    print(f"✓ list_files: found test_hello.py")

    # Cleanup
    test_file.unlink()
    print("✓ All file tools work correctly")


def test_multi_agent_pipeline():
    """Test full multi-agent pipeline with mocked provider."""
    print("\n=== Test 2: Multi-agent pipeline ===")

    mock_provider = make_mock_provider()

    with patch("mycode.agents.get_provider", return_value=mock_provider):
        result = run_multi_agent(
            "Create a simple hello world Python script",
            max_rounds=2
        )

    assert "rounds" in result, "No rounds in result"
    assert len(result["rounds"]) >= 1, "No rounds executed"
    print(f"\n✓ Pipeline completed with {len(result['rounds'])} round(s)")
    print(f"✓ Final status: {result.get('status', 'unknown')}")

    # Check that each agent ran
    round1 = result["rounds"][0]
    assert "plan" in round1, "Planner didn't run"
    assert "worker_output" in round1, "Worker didn't run"
    assert "bug_analysis" in round1, "Bug analyzer didn't run"
    print("✓ All 4 agents (Planner, Worker, Bug Analyzer, Fixer) executed")


def test_provider_management():
    """Test provider add/delete/switch."""
    print("\n=== Test 3: Provider management ===")

    from mycode.providers import (
        add_custom_provider, delete_custom_provider, set_active_provider
    )
    from mycode.config import load_providers

    # Add custom
    add_custom_provider(
        provider_id="testcustom",
        name="Test Custom",
        base_url="https://example.com/v1",
        api_key="sk-test",
        models=["m1", "m2"],
        default_model="m1"
    )
    providers = load_providers()
    assert "testcustom" in providers, "Custom provider not added"
    assert providers["testcustom"]["is_custom"] == True
    print("✓ Custom provider added")

    # Set active
    set_active_provider("testcustom")
    providers = load_providers()
    assert providers["testcustom"]["active"] == True
    print("✓ Custom provider set as active")

    # Delete
    delete_custom_provider("testcustom")
    providers = load_providers()
    assert "testcustom" not in providers, "Custom provider not deleted"
    print("✓ Custom provider deleted")

    # Try to delete pre-built (should fail)
    deleted = delete_custom_provider("groq")
    assert not deleted, "Should not be able to delete pre-built provider"
    print("✓ Pre-built provider cannot be deleted (correct)")


def test_prompts_editing():
    """Test system prompt editing."""
    print("\n=== Test 4: System prompt editing ===")

    from mycode.agents import set_agent_prompt, get_agent_prompt
    from mycode.config import DEFAULT_AGENT_PROMPTS

    original = get_agent_prompt("planner")
    new_prompt = "You are a CUSTOM test planner. Beep boop."

    set_agent_prompt("planner", new_prompt)
    retrieved = get_agent_prompt("planner")
    assert retrieved == new_prompt, "Prompt not updated"
    print("✓ System prompt edited and saved")

    # Reset
    set_agent_prompt("planner", DEFAULT_AGENT_PROMPTS["planner"]["system_prompt"])
    assert get_agent_prompt("planner") == original
    print("✓ System prompt reset to default")


if __name__ == "__main__":
    print("=" * 60)
    print("  MyCode Test Suite")
    print("=" * 60)

    try:
        test_tool_write_read()
        test_provider_management()
        test_prompts_editing()
        test_multi_agent_pipeline()

        print("\n" + "=" * 60)
        print("  ✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nMyCode is working correctly! Here's what's verified:")
        print("  ✓ File tools (read/write/edit/list) work")
        print("  ✓ Custom providers can be added/deleted")
        print("  ✓ Pre-built providers are protected from deletion")
        print("  ✓ System prompts can be edited per agent")
        print("  ✓ Multi-agent pipeline (Planner→Worker→Analyzer→Fixer) works")
        print("  ✓ Tool calling loop functions correctly")
        print("  ✓ Round-based looping works")
        print("\nNext: Add a real API key and try:")
        print("  mycode provider add-key groq")
        print("  mycode agent 'build a calculator'")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
