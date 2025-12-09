
import sys
import os
sys.path.insert(0, ".")
from scripts.llm_backend import LLMBackend

print(f"GEMINI_API_KEY env var present: {'GEMINI_API_KEY' in os.environ}")
if 'GEMINI_API_KEY' in os.environ:
    print(f"Key length: {len(os.environ['GEMINI_API_KEY'])}")
    print(f"Key prefix: {os.environ['GEMINI_API_KEY'][:5]}...")

try:
    llm = LLMBackend()
    print("\nChecking backends in config:")
    for name in ["gemini-flash", "gemini-flash-8b", "openai-mini"]:
        avail = llm.is_available(name)
        print(f"  {name}: {avail}")
        if not avail:
             print(f"    Reason: API Key Env '{llm.get_backend(name).get('api_key_env')}' is {os.getenv(llm.get_backend(name).get('api_key_env'))}")

    print("\nTesting Gemini Flash Generation:")
    try:
        resp, backend, metrics = llm.generate("Say hi", "System prompt", backend_name="gemini-flash")
        print(f"  ✓ Success with {backend}")
        print(f"  Response: {resp}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")

except Exception as e:
    print(f"Initialization failed: {e}")
