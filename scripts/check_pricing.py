#!/usr/bin/env python3
"""
Pricing verification script
Checks API endpoints and web sources to verify pricing is up-to-date
"""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# Import local pricing constants
sys.path.insert(0, str(Path(__file__).parent))
from llm_backend import OPENAI_PRICING, ANTHROPIC_PRICING, GEMINI_PRICING

PROJECT_ROOT = Path(__file__).parent.parent
PRICING_LOG = PROJECT_ROOT / "logs" / "pricing_check.log"


def log_message(message: str):
    """Log to both console and file"""
    print(message)
    PRICING_LOG.parent.mkdir(exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(PRICING_LOG, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def check_openai_pricing():
    """
    Check OpenAI pricing via API models endpoint
    Note: OpenAI doesn't provide pricing in API, must check web
    """
    print("\n📊 OpenAI Pricing Check")
    print("=" * 60)

    try:
        # OpenAI doesn't expose pricing via API
        # Check models endpoint to verify model availability
        response = requests.get(
            "https://api.openai.com/v1/models",
            timeout=5
        )

        if response.status_code == 401:
            print("  ⚠ API key required to check models")
            print("  💡 Manual check required: https://openai.com/api/pricing/")
            return False

        # List local pricing
        print("\n  Current local pricing (per 1M tokens):")
        for model, prices in OPENAI_PRICING.items():
            print(f"    {model:25} Input: ${prices['input']:.3f}  Output: ${prices['output']:.3f}")

        print("\n  ⚠ OpenAI doesn't provide pricing via API")
        print("  📋 Please manually verify at: https://openai.com/api/pricing/")
        return None

    except Exception as e:
        print(f"  ✗ Error checking OpenAI: {e}")
        return False


def check_anthropic_pricing():
    """
    Check Anthropic pricing
    Anthropic doesn't expose pricing via API
    """
    print("\n📊 Anthropic Pricing Check")
    print("=" * 60)

    # List local pricing
    print("\n  Current local pricing (per 1M tokens):")
    for model, prices in ANTHROPIC_PRICING.items():
        print(f"    {model:35} Input: ${prices['input']:.2f}  Output: ${prices['output']:.2f}")

    print("\n  ⚠ Anthropic doesn't provide pricing via API")
    print("  📋 Please manually verify at: https://www.anthropic.com/pricing")
    return None


def check_gemini_pricing():
    """
    Check Gemini pricing
    Google doesn't expose pricing via API endpoint
    """
    print("\n📊 Google Gemini Pricing Check")
    print("=" * 60)

    # List local pricing
    print("\n  Current local pricing (per 1M tokens):")
    for model, prices in GEMINI_PRICING.items():
        print(f"    {model:25} Input: ${prices['input']:.4f}  Output: ${prices['output']:.2f}")

    print("\n  ⚠ Google doesn't provide pricing via API")
    print("  📋 Please manually verify at: https://ai.google.dev/pricing")
    return None


def scrape_openai_pricing_fallback():
    """
    Fallback: Scrape OpenAI pricing page
    This is fragile and may break if page structure changes
    """
    print("\n🔍 Attempting to scrape OpenAI pricing page...")

    try:
        response = requests.get("https://openai.com/api/pricing/", timeout=10)
        if response.status_code == 200:
            # This is very basic - would need HTML parsing for real implementation
            if "gpt-4o-mini" in response.text and "$0.150" in response.text:
                print("  ✓ Pricing page accessible, manual verification recommended")
                return True
            else:
                print("  ⚠ Page structure may have changed")
                return False
        else:
            print(f"  ✗ Failed to access pricing page: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error scraping pricing: {e}")
        return False


def get_pricing_summary():
    """Generate a summary of all pricing"""
    print("\n" + "=" * 60)
    print("💰 PRICING SUMMARY")
    print("=" * 60)

    all_models = []

    # Collect all models
    for model, prices in OPENAI_PRICING.items():
        all_models.append({
            "provider": "OpenAI",
            "model": model,
            "input": prices["input"],
            "output": prices["output"],
            "avg": (prices["input"] + prices["output"]) / 2
        })

    for model, prices in ANTHROPIC_PRICING.items():
        all_models.append({
            "provider": "Anthropic",
            "model": model,
            "input": prices["input"],
            "output": prices["output"],
            "avg": (prices["input"] + prices["output"]) / 2
        })

    for model, prices in GEMINI_PRICING.items():
        all_models.append({
            "provider": "Gemini",
            "model": model,
            "input": prices["input"],
            "output": prices["output"],
            "avg": (prices["input"] + prices["output"]) / 2
        })

    # Sort by average cost
    all_models.sort(key=lambda x: x["avg"])

    print("\nModels ranked by average cost (per 1M tokens):")
    print(f"{'Rank':<6} {'Provider':<12} {'Model':<35} {'Input':>10} {'Output':>10} {'Avg':>10}")
    print("-" * 90)

    for idx, model in enumerate(all_models, 1):
        print(f"{idx:<6} {model['provider']:<12} {model['model']:<35} "
              f"${model['input']:>8.3f}  ${model['output']:>8.2f}  ${model['avg']:>8.2f}")

    print("\n💡 Recommendations based on cost and capability:")
    print("   1. cheapest: gemini-2.0-flash-exp (FREE, experimental)")
    print("   2. best value: gemini-flash-8b ($0.008/project estimated)")
    print("   3. balanced: gemini-1.5-flash ($0.015/project, 1M context)")
    print("   4. small tasks: gpt-4o-mini ($0.012/project, reliable)")
    print("   5. quality: claude-3-5-haiku-latest ($0.25/project, fastest Claude)")


def main():
    print("\n🔍 PBS Wisconsin Editorial Assistant - Pricing Verification")
    print("=" * 60)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    log_message("Starting pricing verification check")

    # Check each provider
    openai_ok = check_openai_pricing()
    anthropic_ok = check_anthropic_pricing()
    gemini_ok = check_gemini_pricing()

    # Show summary
    get_pricing_summary()

    # Final recommendations
    print("\n" + "=" * 60)
    print("📋 ACTION ITEMS")
    print("=" * 60)
    print("\n1. Manual Verification Required:")
    print("   - Visit https://openai.com/api/pricing/")
    print("   - Visit https://www.anthropic.com/pricing")
    print("   - Visit https://ai.google.dev/pricing")
    print("\n2. Update pricing constants in scripts/llm_backend.py if needed")
    print("3. Update 'Last updated' date in pricing comments")
    print("\n4. Recommended to run this check monthly")

    log_message("Pricing verification check completed")
    print(f"\n📝 Log saved to: {PRICING_LOG}")


if __name__ == "__main__":
    main()
