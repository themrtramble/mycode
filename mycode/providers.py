"""
providers.py - LLM Provider management
========================================
Handles all LLM API calls via OpenAI-compatible interface.
"""

import os
from typing import Dict, Any, Optional, List
from openai import OpenAI

from .config import (
    load_providers, save_providers, get_active_provider, set_active_provider
)


class LLMProvider:
    """Wraps an OpenAI-compatible LLM provider."""

    def __init__(self, provider_id: str, base_url: str, api_key: str,
                 model: str, name: str = ""):
        self.provider_id = provider_id
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.name = name or provider_id
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(self, messages: List[Dict[str, str]],
             temperature: float = 0.7,
             max_tokens: int = 2048,
             tools: Optional[List] = None):
        """Send chat messages and return assistant message object."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message

    def chat_simple(self, system: str, user: str,
                    temperature: float = 0.7,
                    max_tokens: int = 2048) -> str:
        """Simple one-shot chat. Returns text only."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
        msg = self.chat(messages, temperature, max_tokens)
        return msg.content or ""


def get_provider(provider_id: Optional[str] = None,
                 model: Optional[str] = None) -> Optional[LLMProvider]:
    """Get an LLMProvider instance."""
    providers = load_providers()

    if provider_id:
        if provider_id not in providers:
            print(f"❌ Provider '{provider_id}' not found.")
            return None
        p = providers[provider_id]
    else:
        active = get_active_provider()
        if not active:
            print("❌ No active provider. Run: mycode provider add-key <id>")
            return None
        provider_id = active["id"]
        p = active

    if not p.get("api_key"):
        print(f"❌ Provider '{provider_id}' has no API key set.")
        print(f"   Run: mycode provider add-key {provider_id}")
        return None

    use_model = model or p.get("default_model") or p.get("models", [""])[0]
    return LLMProvider(
        provider_id=provider_id,
        base_url=p["base_url"],
        api_key=p["api_key"],
        model=use_model,
        name=p.get("name", provider_id)
    )


def list_providers() -> None:
    """Print all configured providers."""
    providers = load_providers()
    print("\n" + "=" * 80)
    print(f"{'ID':<15}{'Name':<22}{'API Key':<10}{'Active':<8}{'Default Model'}")
    print("=" * 80)
    for pid, p in providers.items():
        has_key = "✓ Yes" if p.get("api_key") else "✗ No"
        active = "✓" if p.get("active") else ""
        custom = " (custom)" if p.get("is_custom") else ""
        model = p.get("default_model", "")[:30]
        print(f"{pid:<15}{p.get('name', '')[:20]+custom:<22}{has_key:<10}{active:<8}{model}")
    print("=" * 80 + "\n")


def add_custom_provider(provider_id: str, name: str, base_url: str,
                       api_key: str, models: List[str],
                       default_model: str) -> bool:
    """Add a custom provider."""
    providers = load_providers()
    if provider_id in providers and not providers[provider_id].get("is_custom"):
        print(f"❌ Cannot overwrite pre-built provider '{provider_id}'.")
        return False
    providers[provider_id] = {
        "name": name,
        "base_url": base_url,
        "api_key": api_key,
        "models": models,
        "default_model": default_model,
        "is_custom": True,
        "active": False
    }
    save_providers(providers)
    print(f"✅ Custom provider '{provider_id}' added.")
    return True


def delete_custom_provider(provider_id: str) -> bool:
    """Delete a custom provider."""
    providers = load_providers()
    if provider_id not in providers:
        print(f"❌ Provider '{provider_id}' not found.")
        return False
    if not providers[provider_id].get("is_custom"):
        print(f"❌ Cannot delete pre-built provider '{provider_id}'.")
        return False
    del providers[provider_id]
    save_providers(providers)
    print(f"✅ Custom provider '{provider_id}' deleted.")
    return True


def set_api_key(provider_id: str, api_key: str) -> bool:
    """Set/update API key for a provider."""
    providers = load_providers()
    if provider_id not in providers:
        print(f"❌ Provider '{provider_id}' not found.")
        return False
    providers[provider_id]["api_key"] = api_key
    save_providers(providers)
    print(f"✅ API key set for '{provider_id}'.")
    return True


def set_default_model(provider_id: str, model: str) -> bool:
    """Set default model for a provider."""
    providers = load_providers()
    if provider_id not in providers:
        print(f"❌ Provider '{provider_id}' not found.")
        return False
    if model not in providers[provider_id].get("models", []):
        print(f"⚠️  Model '{model}' not in known models list, but setting anyway.")
    providers[provider_id]["default_model"] = model
    save_providers(providers)
    print(f"✅ Default model for '{provider_id}' set to '{model}'.")
    return True
