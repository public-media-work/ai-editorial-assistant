#!/usr/bin/env python3
"""
Portable LLM backend manager
Handles local, remote, and API-based LLM calls uniformly
"""

import requests
import json
import os
from pathlib import Path
from typing import Dict, Optional, NamedTuple

class UsageMetrics(NamedTuple):
    """Token usage and cost metrics for an LLM call"""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    model: str
    backend: str

# Try to load .env file
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent
    load_dotenv(project_root / ".env")
except ImportError:
    pass  # python-dotenv not installed, continuing without it

# OpenAI pricing per 1M tokens (as of 2024)
# https://openai.com/api/pricing/
OPENAI_PRICING = {
    "gpt-4o-mini": {"input": 0.150, "output": 0.600},  # per 1M tokens
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-2024-11-20": {"input": 2.50, "output": 10.00},
}

# Anthropic pricing per 1M tokens
# https://www.anthropic.com/pricing
ANTHROPIC_PRICING = {
    "claude-3-5-sonnet-latest": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-latest": {"input": 1.00, "output": 5.00},
}

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

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD based on model pricing"""
        # Check OpenAI pricing
        if model in OPENAI_PRICING:
            pricing = OPENAI_PRICING[model]
            input_cost = (input_tokens / 1_000_000) * pricing["input"]
            output_cost = (output_tokens / 1_000_000) * pricing["output"]
            return input_cost + output_cost

        # Check Anthropic pricing
        if model in ANTHROPIC_PRICING:
            pricing = ANTHROPIC_PRICING[model]
            input_cost = (input_tokens / 1_000_000) * pricing["input"]
            output_cost = (output_tokens / 1_000_000) * pricing["output"]
            return input_cost + output_cost

        # Unknown model - return 0
        return 0.0

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

    def call_ollama(self, backend: Dict, prompt: str, system: str) -> tuple[str, UsageMetrics]:
        """Call Ollama endpoint (local or remote) - returns response with zero-cost metrics"""
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

        data = response.json()
        content = data["response"]

        # Ollama doesn't provide token counts in the same way, use zero metrics
        metrics = UsageMetrics(
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            estimated_cost=0.0,
            model=backend["model"],
            backend="ollama"
        )

        print(f"    Ollama response received (local/free)")

        return content, metrics

    def call_openai(self, backend: Dict, prompt: str, system: str) -> tuple[str, UsageMetrics]:
        """Call OpenAI API and return response with usage metrics"""
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

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        # Extract usage data
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

        # Calculate cost
        model = backend["model"]
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        metrics = UsageMetrics(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=cost,
            model=model,
            backend="openai"
        )

        print(f"    Tokens: {input_tokens} in + {output_tokens} out = {total_tokens} total (${cost:.4f})")

        return content, metrics

    def call_anthropic(self, backend: Dict, prompt: str, system: str) -> tuple[str, UsageMetrics]:
        """Call Anthropic API and return response with usage metrics"""
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

        data = response.json()
        content = data["content"][0]["text"]

        # Extract usage data
        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        total_tokens = input_tokens + output_tokens

        # Calculate cost
        model = backend["model"]
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        metrics = UsageMetrics(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=cost,
            model=model,
            backend="anthropic"
        )

        print(f"    Tokens: {input_tokens} in + {output_tokens} out = {total_tokens} total (${cost:.4f})")

        return content, metrics

    def generate(self, prompt: str, system: str,
                 backend_name: Optional[str] = None) -> tuple[str, str, UsageMetrics]:
        """
        Generate response using specified or auto-selected backend

        Returns:
            tuple: (response_text, backend_name_used, usage_metrics)
        """
        if backend_name is None:
            backend_name = self.select_backend()

        backend = self.get_backend(backend_name)

        print(f"\n  Using backend: {backend_name}")

        # Route to appropriate handler based on type
        if backend["type"] == "ollama":
            response, metrics = self.call_ollama(backend, prompt, system)
        elif backend["type"] == "openai":
            response, metrics = self.call_openai(backend, prompt, system)
        elif backend["type"] == "anthropic":
            response, metrics = self.call_anthropic(backend, prompt, system)
        else:
            raise Exception(f"Unknown backend type: {backend['type']}")

        return response, backend_name, metrics


if __name__ == "__main__":
    # Test script
    print("Testing LLM Backend Manager")
    print("="*60)

    llm = LLMBackend()

    test_system = "You are a helpful assistant."
    test_prompt = "Say hello and confirm you're working correctly in one sentence."

    try:
        response, backend, metrics = llm.generate(test_prompt, test_system)
        print(f"\n✓ Success!")
        print(f"Backend used: {backend}")
        print(f"\nUsage Metrics:")
        print(f"  Input tokens: {metrics.input_tokens}")
        print(f"  Output tokens: {metrics.output_tokens}")
        print(f"  Total tokens: {metrics.total_tokens}")
        print(f"  Estimated cost: ${metrics.estimated_cost:.4f}")
        print(f"  Model: {metrics.model}")
        print(f"\nResponse:\n{response}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
