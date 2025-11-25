#!/usr/bin/env python3
"""
Portable LLM backend manager
Handles local, remote, and API-based LLM calls uniformly
"""

import requests
import json
import os
from pathlib import Path
from typing import Dict, Optional

# Try to load .env file
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent
    load_dotenv(project_root / ".env")
except ImportError:
    pass  # python-dotenv not installed, continuing without it

class LLMBackend:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Default to config/llm-config.json relative to script location
            script_dir = Path(__file__).parent.parent
            config_path = script_dir / "config" / "llm-config.json"

        with open(config_path) as f:
            self.config = json.load(f)

    def get_backend(self, backend_name: str) -> Dict:
        """Get backend configuration"""
        if backend_name not in self.config["backends"]:
            raise ValueError(f"Backend '{backend_name}' not found in config")
        return self.config["backends"][backend_name]

    def is_available(self, backend_name: str) -> bool:
        """Check if backend is reachable"""
        backend = self.get_backend(backend_name)

        # Check if explicitly disabled
        if not backend.get("enabled", True):
            return False

        if backend["type"] == "ollama":
            # Try to reach Ollama endpoint
            try:
                response = requests.get(
                    f"{backend['endpoint']}/api/tags",
                    timeout=2
                )
                return response.status_code == 200
            except Exception as e:
                print(f"  ✗ {backend_name} unavailable: {e}")
                return False

        elif backend["type"] in ["openai", "anthropic"]:
            # Check if API key exists
            api_key_env = backend.get("api_key_env")
            has_key = api_key_env and os.getenv(api_key_env) is not None
            if not has_key:
                print(f"  ✗ {backend_name} unavailable: API key not found (${api_key_env})")
            return has_key

        return False

    def select_backend(self) -> str:
        """Auto-select best available backend"""
        if self.config["auto_select"]["enabled"]:
            print("\nChecking available backends...")
            for backend_name in self.config["auto_select"]["preference_order"]:
                if backend_name not in self.config["backends"]:
                    continue

                print(f"  → Checking {backend_name}...", end=" ")
                if self.is_available(backend_name):
                    backend = self.get_backend(backend_name)
                    cost = backend.get("cost_per_project", 0)
                    print(f"✓ Available (${cost:.3f}/project)")
                    return backend_name

            raise Exception("No backends available! Check config and API keys.")
        else:
            return self.config["primary_backend"]

    def call_ollama(self, backend: Dict, prompt: str, system: str) -> str:
        """Call Ollama endpoint (local or remote)"""
        print(f"    Calling Ollama at {backend['endpoint']}...")

        response = requests.post(
            f"{backend['endpoint']}/api/generate",
            json={
                "model": backend["model"],
                "prompt": f"{system}\n\n{prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            },
            timeout=backend["timeout"]
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

        return response.json()["response"]

    def call_openai(self, backend: Dict, prompt: str, system: str) -> str:
        """Call OpenAI API"""
        print(f"    Calling OpenAI ({backend['model']})...")

        api_key = os.getenv(backend["api_key_env"])

        response = requests.post(
            backend["endpoint"],
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": backend["model"],
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            },
            timeout=backend["timeout"]
        )

        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

        return response.json()["choices"][0]["message"]["content"]

    def call_anthropic(self, backend: Dict, prompt: str, system: str) -> str:
        """Call Anthropic API"""
        print(f"    Calling Anthropic ({backend['model']})...")

        api_key = os.getenv(backend["api_key_env"])

        response = requests.post(
            backend["endpoint"],
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": backend["model"],
                "max_tokens": 8192,
                "system": system,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            },
            timeout=backend["timeout"]
        )

        if response.status_code != 200:
            raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")

        return response.json()["content"][0]["text"]

    def generate(self, prompt: str, system: str,
                 backend_name: Optional[str] = None) -> tuple[str, str]:
        """
        Generate response using specified or auto-selected backend

        Returns:
            tuple: (response_text, backend_name_used)
        """
        if backend_name is None:
            backend_name = self.select_backend()

        backend = self.get_backend(backend_name)

        print(f"\n  Using backend: {backend_name}")

        # Route to appropriate handler based on type
        if backend["type"] == "ollama":
            response = self.call_ollama(backend, prompt, system)
        elif backend["type"] == "openai":
            response = self.call_openai(backend, prompt, system)
        elif backend["type"] == "anthropic":
            response = self.call_anthropic(backend, prompt, system)
        else:
            raise Exception(f"Unknown backend type: {backend['type']}")

        return response, backend_name


if __name__ == "__main__":
    # Test script
    print("Testing LLM Backend Manager")
    print("="*60)

    llm = LLMBackend()

    test_system = "You are a helpful assistant."
    test_prompt = "Say hello and confirm you're working correctly in one sentence."

    try:
        response, backend = llm.generate(test_prompt, test_system)
        print(f"\n✓ Success!")
        print(f"Backend used: {backend}")
        print(f"\nResponse:\n{response}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
