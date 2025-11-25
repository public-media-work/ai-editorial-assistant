# Fully Automated Processing Plan

**Status**: Design document for future implementation
**Current**: Semi-automatic (manual command in Claude Code)
**Future**: Fully automatic with portable LLM architecture

---

## Architecture Overview

### Design Principles

1. **Location-agnostic**: LLM can run locally or on remote server
2. **Model-agnostic**: Easy to switch between local/OpenAI/Claude
3. **Zero-config migration**: Move LLM to another machine without code changes
4. **Graceful fallback**: If primary LLM unavailable, fall back to API
5. **Cost-optimized**: Use cheapest available option automatically

### Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: WATCHER (This Mac - Always)                       │
│  ├─ Detects new transcripts                                │
│  ├─ Creates project structure                              │
│  └─ Adds to processing queue                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  TIER 2: ORCHESTRATOR (This Mac - Always)                  │
│  ├─ Reads processing queue                                 │
│  ├─ Determines which LLM to use (local/remote/API)        │
│  ├─ Routes requests to appropriate endpoint                │
│  └─ Handles retries and fallbacks                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  TIER 3: LLM BACKENDS (Portable)                           │
│  ├─ Option A: Local Ollama (http://localhost:11434)       │
│  ├─ Option B: Remote Ollama (http://homeserver:11434)     │
│  ├─ Option C: OpenAI API (https://api.openai.com)         │
│  └─ Option D: Anthropic API (https://api.anthropic.com)   │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration System

### Single Config File

`config/llm-config.json`:
```json
{
  "primary_backend": "local-ollama",
  "fallback_backend": "openai-mini",

  "backends": {
    "local-ollama": {
      "type": "ollama",
      "endpoint": "http://localhost:11434",
      "model": "qwen2.5:14b",
      "timeout": 120,
      "cost_per_project": 0.00
    },
    "remote-ollama": {
      "type": "ollama",
      "endpoint": "http://192.168.1.100:11434",
      "model": "qwen2.5:14b",
      "timeout": 120,
      "cost_per_project": 0.00
    },
    "openai-mini": {
      "type": "openai",
      "endpoint": "https://api.openai.com/v1/chat/completions",
      "model": "gpt-4o-mini",
      "api_key_env": "OPENAI_API_KEY",
      "timeout": 30,
      "cost_per_project": 0.007
    },
    "openai": {
      "type": "openai",
      "endpoint": "https://api.openai.com/v1/chat/completions",
      "model": "gpt-4o",
      "api_key_env": "OPENAI_API_KEY",
      "timeout": 30,
      "cost_per_project": 0.12
    },
    "claude": {
      "type": "anthropic",
      "endpoint": "https://api.anthropic.com/v1/messages",
      "model": "claude-3-5-sonnet-20241022",
      "api_key_env": "ANTHROPIC_API_KEY",
      "timeout": 30,
      "cost_per_project": 0.17
    }
  },

  "auto_select": {
    "enabled": true,
    "preference_order": [
      "local-ollama",
      "remote-ollama",
      "openai-mini",
      "openai",
      "claude"
    ],
    "check_interval_seconds": 5
  },

  "processing": {
    "check_queue_interval_seconds": 300,
    "batch_size": 4,
    "parallel_processing": true
  }
}
```

### Migration Process

**Testing phase (today)**:
```json
"primary_backend": "local-ollama"
```

**Move to spare M1 MacBook**:
```json
"primary_backend": "remote-ollama",
"backends": {
  "remote-ollama": {
    "endpoint": "http://macbook-server.local:11434"
  }
}
```

**Move to Proxmox VM**:
```json
"primary_backend": "remote-ollama",
"backends": {
  "remote-ollama": {
    "endpoint": "http://proxmox-vm.local:11434"
  }
}
```

**Change entire config**: Just edit one JSON file, no code changes.

---

## Component Design

### 1. LLM Backend Manager

**File**: `scripts/llm_backend.py`

```python
#!/usr/bin/env python3
"""
Portable LLM backend manager
Handles local, remote, and API-based LLM calls uniformly
"""

import requests
import json
import os
from typing import Dict, Optional

class LLMBackend:
    def __init__(self, config_path: str = "config/llm-config.json"):
        with open(config_path) as f:
            self.config = json.load(f)

    def get_backend(self, backend_name: str) -> Dict:
        """Get backend configuration"""
        return self.config["backends"][backend_name]

    def is_available(self, backend_name: str) -> bool:
        """Check if backend is reachable"""
        backend = self.get_backend(backend_name)

        if backend["type"] == "ollama":
            # Try to reach Ollama endpoint
            try:
                response = requests.get(
                    f"{backend['endpoint']}/api/tags",
                    timeout=2
                )
                return response.status_code == 200
            except:
                return False

        elif backend["type"] in ["openai", "anthropic"]:
            # Check if API key exists
            api_key_env = backend.get("api_key_env")
            return api_key_env and os.getenv(api_key_env) is not None

        return False

    def select_backend(self) -> str:
        """Auto-select best available backend"""
        if self.config["auto_select"]["enabled"]:
            for backend_name in self.config["auto_select"]["preference_order"]:
                if self.is_available(backend_name):
                    print(f"✓ Selected backend: {backend_name}")
                    return backend_name

            raise Exception("No backends available!")
        else:
            return self.config["primary_backend"]

    def call_ollama(self, backend: Dict, prompt: str, system: str) -> str:
        """Call Ollama endpoint (local or remote)"""
        response = requests.post(
            f"{backend['endpoint']}/api/generate",
            json={
                "model": backend["model"],
                "prompt": prompt,
                "system": system,
                "stream": False
            },
            timeout=backend["timeout"]
        )
        return response.json()["response"]

    def call_openai(self, backend: Dict, prompt: str, system: str) -> str:
        """Call OpenAI API"""
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
                ]
            },
            timeout=backend["timeout"]
        )
        return response.json()["choices"][0]["message"]["content"]

    def call_anthropic(self, backend: Dict, prompt: str, system: str) -> str:
        """Call Anthropic API"""
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
                "max_tokens": 4096,
                "system": system,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=backend["timeout"]
        )
        return response.json()["content"][0]["text"]

    def generate(self, prompt: str, system: str,
                 backend_name: Optional[str] = None) -> str:
        """
        Generate response using specified or auto-selected backend

        This is the main method - location-agnostic
        """
        if backend_name is None:
            backend_name = self.select_backend()

        backend = self.get_backend(backend_name)

        # Route to appropriate handler based on type
        if backend["type"] == "ollama":
            return self.call_ollama(backend, prompt, system)
        elif backend["type"] == "openai":
            return self.call_openai(backend, prompt, system)
        elif backend["type"] == "anthropic":
            return self.call_anthropic(backend, prompt, system)

        raise Exception(f"Unknown backend type: {backend['type']}")
```

**Key features**:
- ✅ Single interface for all backends
- ✅ Location-agnostic (localhost vs remote vs API)
- ✅ Auto-selection with fallback
- ✅ Health checking
- ✅ Zero code changes to migrate

---

### 2. Automated Queue Processor

**File**: `scripts/process_queue_auto.py`

```python
#!/usr/bin/env python3
"""
Automated queue processor
Runs agents on all queued projects using configured LLM backend
"""

import json
import time
from pathlib import Path
from llm_backend import LLMBackend

PROJECT_ROOT = Path(__file__).parent.parent
QUEUE_FILE = PROJECT_ROOT / ".processing-requests.json"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"

def load_queue():
    """Load processing queue"""
    if not QUEUE_FILE.exists():
        return []
    with open(QUEUE_FILE) as f:
        return json.load(f)

def load_agent_prompt(agent_name: str) -> str:
    """Load agent markdown file"""
    agent_file = AGENTS_DIR / f"{agent_name}.md"
    with open(agent_file) as f:
        return f.read()

def load_transcript(project_name: str) -> str:
    """Load transcript content"""
    # Try transcripts directory first
    transcript_path = PROJECT_ROOT / "transcripts" / f"{project_name}_ForClaude.txt"

    if not transcript_path.exists():
        # Try archive
        transcript_path = PROJECT_ROOT / "transcripts" / "archive" / f"{project_name}_ForClaude.txt"

    with open(transcript_path) as f:
        return f.read()

def process_project(project_name: str, llm: LLMBackend):
    """Process a single project with both agents"""
    print(f"\n{'='*60}")
    print(f"Processing: {project_name}")
    print(f"{'='*60}\n")

    # Load transcript
    transcript = load_transcript(project_name)

    # Load agent prompts
    analyst_prompt = load_agent_prompt("transcript-analyst")
    formatter_prompt = load_agent_prompt("formatter")

    # Run transcript-analyst
    print("→ Running transcript-analyst...")
    analyst_system = "You are a professional video content analyst generating SEO metadata."
    analyst_user = f"{analyst_prompt}\n\n# TRANSCRIPT\n\n{transcript}"

    brainstorming = llm.generate(analyst_user, analyst_system)

    # Save brainstorming
    output_dir = PROJECT_ROOT / "OUTPUT" / project_name
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "brainstorming.md", "w") as f:
        f.write(brainstorming)
    print(f"  ✓ Saved: brainstorming.md")

    # Run formatter
    print("→ Running formatter...")
    formatter_system = "You are a professional transcript formatter applying AP Style."
    formatter_user = f"{formatter_prompt}\n\n# TRANSCRIPT\n\n{transcript}"

    formatted_output = llm.generate(formatter_user, formatter_system)

    # Parse formatter output (contains both formatted transcript and timestamps)
    # For now, save as single file - can split later
    with open(output_dir / "formatted_transcript.md", "w") as f:
        f.write(formatted_output)
    print(f"  ✓ Saved: formatted_transcript.md")

    # Update manifest
    # ... (manifest update logic)

    print(f"\n✓ {project_name} complete\n")

def main():
    """Main automation loop"""
    print("="*60)
    print("AUTOMATED QUEUE PROCESSOR")
    print("="*60)

    # Initialize LLM backend
    llm = LLMBackend()

    # Load queue
    queue = load_queue()

    if not queue:
        print("\n✓ Queue is empty - nothing to process")
        return

    print(f"\nFound {len(queue)} project(s) in queue:")
    for item in queue:
        print(f"  • {item['project']}")

    print("\nStarting processing...")

    # Process each project
    for item in queue:
        try:
            process_project(item['project'], llm)
        except Exception as e:
            print(f"✗ Error processing {item['project']}: {e}")

    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print("\nNext step: Run ./scripts/finalize-queue.sh to archive")

if __name__ == "__main__":
    main()
```

---

### 3. Scheduled Automation (Optional)

**File**: `scripts/scheduled_processor.sh`

```bash
#!/bin/bash
# Scheduled processor - runs periodically to check queue
# Can be triggered by LaunchAgent or cron

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check if queue has items
queue_count=$(cat .processing-requests.json | jq 'length')

if [ "$queue_count" -gt 0 ]; then
  echo "$(date): Found $queue_count items in queue, processing..."

  # Run automated processor
  python3 scripts/process_queue_auto.py

  # Finalize (archive transcripts)
  ./scripts/finalize-queue.sh

  echo "$(date): Processing complete"
else
  echo "$(date): Queue empty, nothing to process"
fi
```

**LaunchAgent** for automatic scheduling:

`~/Library/LaunchAgents/com.editorial-assistant.queue-processor.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.editorial-assistant.queue-processor</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/mriechers/Developer/editorial-assistant/scripts/scheduled_processor.sh</string>
    </array>

    <key>StartInterval</key>
    <integer>1800</integer> <!-- Run every 30 minutes -->

    <key>RunAtLoad</key>
    <false/>

    <key>StandardOutPath</key>
    <string>/Users/mriechers/Developer/editorial-assistant/logs/processor.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/mriechers/Developer/editorial-assistant/logs/processor.error.log</string>
</dict>
</plist>
```

---

## LLM Hosting Options

### Option A: Local (Testing - Now)

**Setup**:
```bash
# Install Ollama
brew install ollama

# Start Ollama service
ollama serve

# Pull recommended model
ollama pull qwen2.5:14b
```

**Config**:
```json
"primary_backend": "local-ollama"
```

**Pros**:
- ✅ Testing on this Mac
- ✅ Instant setup
- ✅ $0 cost

**Cons**:
- ❌ Uses your work Mac's resources
- ❌ Only runs when Mac is on

---

### Option B: Spare M1 MacBook (Simple Migration)

**Setup on MacBook**:
```bash
# Install Ollama
brew install ollama

# Configure to listen on network
# Edit: ~/Library/LaunchAgents/com.ollama.ollama.plist
# Add environment variable:
# OLLAMA_HOST=0.0.0.0:11434

# Reload and start
launchctl unload ~/Library/LaunchAgents/com.ollama.ollama.plist
launchctl load ~/Library/LaunchAgents/com.ollama.ollama.plist

# Pull model
ollama pull qwen2.5:14b
```

**Config on work Mac**:
```json
"primary_backend": "remote-ollama",
"backends": {
  "remote-ollama": {
    "endpoint": "http://macbook-server.local:11434"
  }
}
```

**Pros**:
- ✅ Dedicated hardware
- ✅ Runs 24/7
- ✅ Free up work Mac resources
- ✅ Still $0 cost

**Cons**:
- ❌ M1 MacBook needs to stay on
- ❌ Network dependency

---

### Option C: Proxmox VM (Advanced)

**Two approaches**:

#### C1: macOS VM in Proxmox
**Complexity**: High
**Performance**: Good
**Ollama support**: Native (macOS)

**Setup**:
1. Create macOS VM in Proxmox
2. Install Ollama in VM
3. Configure network access
4. Same config as Option B

**Pros**:
- ✅ Runs on your existing server
- ✅ Native Ollama support
- ✅ Can allocate specific resources

**Cons**:
- ❌ macOS VM in Proxmox is complex
- ❌ Licensing considerations
- ❌ May not utilize GPU well

#### C2: Linux VM with Ollama
**Complexity**: Medium
**Performance**: Excellent
**Ollama support**: Native (Linux)

**Setup**:
```bash
# In Proxmox, create Ubuntu VM with:
# - 8+ CPU cores
# - 32GB+ RAM
# - GPU passthrough (if available)

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure for network access
export OLLAMA_HOST=0.0.0.0:11434
ollama serve &

# Pull model
ollama pull qwen2.5:14b
```

**Config on work Mac**:
```json
"primary_backend": "remote-ollama",
"backends": {
  "remote-ollama": {
    "endpoint": "http://proxmox-ubuntu.local:11434"
  }
}
```

**Pros**:
- ✅ Best performance
- ✅ Runs on existing infrastructure
- ✅ Can use GPU if passed through
- ✅ Easier than macOS VM

**Cons**:
- ❌ Need to allocate VM resources
- ❌ Network dependency

---

## Migration Path

### Phase 1: Local Testing (This Week)
```bash
# On this Mac
brew install ollama
ollama serve
ollama pull qwen2.5:14b

# Test quality
python3 scripts/process_queue_auto.py

# Compare output to Claude/GPT
```

**Config**:
```json
"primary_backend": "local-ollama"
```

### Phase 2: Move to Spare MacBook (Next Week)
```bash
# On MacBook server
brew install ollama
# Configure for network access
ollama serve
ollama pull qwen2.5:14b
```

**Config change** (only this):
```json
"primary_backend": "remote-ollama",
"backends": {
  "remote-ollama": {
    "endpoint": "http://macbook-server.local:11434"
  }
}
```

### Phase 3: Move to Proxmox (Future)
```bash
# Create Ubuntu VM
# Install Ollama
# Configure networking
```

**Config change** (only this):
```json
"backends": {
  "remote-ollama": {
    "endpoint": "http://proxmox-ubuntu.local:11434"
  }
}
```

**Zero code changes required** - just update endpoint URL.

---

## Fallback Strategy

### Multi-Tier Fallback

**Configuration**:
```json
"auto_select": {
  "enabled": true,
  "preference_order": [
    "remote-ollama",      // Try remote first (free)
    "local-ollama",       // Try local (free)
    "openai-mini",        // Fallback to cheap API ($0.007)
    "claude"              // Last resort ($0.17)
  ]
}
```

**What happens**:
1. Script tries `remote-ollama` (Proxmox/MacBook)
2. If unreachable → tries `local-ollama` (this Mac)
3. If Ollama not running → uses `openai-mini` API
4. If API key missing → uses `claude`

**Result**: Nearly 100% uptime with cost optimization

---

## Cost Comparison

| Scenario | Cost/Month (50 projects) | Infrastructure |
|----------|--------------------------|----------------|
| **Local Ollama** | $0.50 (electricity) | This Mac |
| **Remote Ollama (MacBook)** | $2.00 (electricity) | Spare MacBook |
| **Remote Ollama (Proxmox)** | $0.00 (already running) | Existing server |
| **GPT-4o mini fallback** | $0.35 | Cloud |
| **Claude Sonnet** | $8.50 | Cloud |
| **Semi-automatic (current)** | $0.00 | Manual |

**Recommendation**: Start with local, move to Proxmox (best of all worlds)

---

## Implementation Checklist

### Immediate (Testing)
- [ ] Install Ollama on this Mac
- [ ] Pull qwen2.5:14b model
- [ ] Create `config/llm-config.json`
- [ ] Create `scripts/llm_backend.py`
- [ ] Create `scripts/process_queue_auto.py`
- [ ] Test on existing queue (4 projects)
- [ ] Compare quality to Claude output

### Short-term (Production)
- [ ] Set up spare M1 MacBook as LLM server
- [ ] Configure Ollama for network access
- [ ] Update config to point to MacBook
- [ ] Test remote processing
- [ ] Set up LaunchAgent for automatic processing

### Long-term (Optimal)
- [ ] Create Ubuntu VM in Proxmox
- [ ] Install Ollama with GPU passthrough
- [ ] Migrate LLM to Proxmox
- [ ] Update config endpoint
- [ ] Monitor performance and costs

---

## Quality Assurance

### Testing Protocol

Before switching to automated:

1. **Process 5 test transcripts** with local LLM
2. **Compare to Claude output** side-by-side:
   - Title creativity
   - Description accuracy
   - Keyword relevance
   - AP Style compliance
   - Formatting consistency
3. **If quality ≥80%** → proceed with automation
4. **If quality <80%** → try larger model or use API fallback

### Quality Thresholds

| Metric | Acceptable | Ideal |
|--------|-----------|-------|
| Title accuracy | 80% | 95% |
| Formatting errors | <5% | <1% |
| AP Style compliance | 85% | 98% |
| Processing speed | <2 min | <1 min |

---

## Support & Maintenance

### Monitoring

**Daily check** (automated):
```bash
# Check backend health
curl http://remote-server:11434/api/tags

# Check queue status
cat .processing-requests.json | jq 'length'

# Check recent processing
tail logs/processor.log
```

### Troubleshooting

**LLM server unreachable**:
```bash
# Check if Ollama running on server
ssh server "ps aux | grep ollama"

# Restart if needed
ssh server "pkill ollama && ollama serve &"
```

**Automatic fallback to API**:
- Check logs for backend selection
- System will use GPT-4o mini automatically
- Cost will increase but processing continues

---

## Summary

**Architecture**: Three-tier (watcher → orchestrator → LLM backend)
**Portability**: Config-based, zero code changes to migrate
**Cost**: $0 (local/Proxmox) to $0.35/month (API fallback)
**Quality**: Test local first, automatic API fallback if needed
**Migration**: localhost → MacBook → Proxmox (just update config)

**Next step**: Install Ollama locally and test quality with your existing queue.
