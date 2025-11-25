# Local LLM Setup - Complete!

**Status**: ✅ Ready to test
**Model**: Qwen 2.5 14B (9GB)
**Cost**: $0

---

## What's Installed

### 1. Ollama Server
- **Location**: http://localhost:11434
- **Model**: qwen2.5:14b (9GB)
- **Status**: Running
- **Auto-start**: Can be configured (see below)

### 2. Python Scripts
- **`scripts/llm_backend.py`** - Portable backend manager
- **`scripts/process_queue_auto.py`** - Automated queue processor
- **`config/llm-config.json`** - Configuration file

### 3. Virtual Environment
- **Location**: `/venv/`
- **Packages**: requests
- **Activate**: `source venv/bin/activate`

---

## Testing the System

### Quick Test (Already Passed!)
```bash
source venv/bin/activate
python3 scripts/llm_backend.py
```

**Result**: ✅ Connected to Ollama, test passed!

### Process Your Queue (4 Projects)
```bash
source venv/bin/activate
python3 scripts/process_queue_auto.py
```

This will:
1. Auto-select local Ollama backend (free!)
2. Load your 4 queued projects:
   - 2BUC0000HDDVD01
   - 2BUC0000HDDVD02
   - 2BUC0000HDDVD03
   - 2BUC0000HDWEB01
3. Run transcript-analyst on each
4. Run formatter on each
5. Save all deliverables

**Estimated time**: 5-8 minutes total (all 4 projects)

---

## Configuration

### Current Setup (config/llm-config.json)
```json
{
  "primary_backend": "local-ollama",
  "backends": {
    "local-ollama": {
      "endpoint": "http://localhost:11434",
      "model": "qwen2.5:14b",
      "cost_per_project": 0.00
    }
  }
}
```

### Future Migration

**Move to spare MacBook**:
Just update the endpoint:
```json
"remote-ollama": {
  "endpoint": "http://macbook-server.local:11434"
}
```

**Move to Proxmox**:
```json
"remote-ollama": {
  "endpoint": "http://proxmox-vm.local:11434"
}
```

**Add API fallback** (if Ollama down):
Already configured! If local Ollama fails, automatically falls back to:
1. Remote Ollama (if configured)
2. OpenAI mini ($0.007/project)
3. Claude ($0.17/project)

Just set the API key:
```bash
export OPENAI_API_KEY="your-key-here"
```

---

## Auto-Start Ollama (Optional)

### Option 1: LaunchAgent (Always Running)
Create `~/Library/LaunchAgents/com.ollama.server.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/ollama</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Then:
```bash
launchctl load ~/Library/LaunchAgents/com.ollama.server.plist
```

### Option 2: Manual (When Needed)
```bash
ollama serve &
```

---

## Workflow Options

### Semi-Automatic (Current)
1. Drop transcripts → watcher queues them
2. When convenient, run: `python3 scripts/process_queue_auto.py`
3. Archives automatically via: `./scripts/finalize-queue.sh`

**Cost**: $0
**Control**: Full
**Time**: ~30 seconds of your time per batch

### Fully Automatic (Future)
Set up LaunchAgent to run `process_queue_auto.py` every 30 minutes:
```xml
<key>StartInterval</key>
<integer>1800</integer>
```

**Cost**: $0
**Control**: Automatic
**Time**: Zero intervention

---

## Quality Testing Plan

Before committing to full automation:

### 1. Process One Project First
```bash
# Edit .processing-requests.json to only include one project
source venv/bin/activate
python3 scripts/process_queue_auto.py
```

### 2. Compare to Claude Output
- Check brainstorming quality
- Review formatted transcript
- Verify AP Style compliance
- Compare creativity/accuracy

### 3. If Quality Good (>80%)
- Process all 4 projects
- Use for real work
- Consider full automation

### 4. If Quality Not Sufficient
- Try larger model: `ollama pull qwen2.5:32b`
- Or fallback to API: Set `OPENAI_API_KEY`
- System will auto-select best option

---

## Commands Cheat Sheet

### Run Queue Processor
```bash
cd /Users/mriechers/Developer/editorial-assistant
source venv/bin/activate
python3 scripts/process_queue_auto.py
```

### Check Ollama Status
```bash
ollama list                    # List models
ollama ps                      # Running models
curl http://localhost:11434    # Server status
```

### View Queue
```bash
cat .processing-requests.json | jq '.'
```

### Finalize & Archive
```bash
./scripts/finalize-queue.sh
```

### Switch Models
```bash
# Try different model
ollama pull llama3.1:8b

# Update config
# Edit config/llm-config.json, change model to "llama3.1:8b"
```

---

## Cost Comparison

| Approach | Setup | Per Project | 50 Projects/Month |
|----------|-------|-------------|-------------------|
| **Local Ollama** | ✅ Done | $0.00 | $0.00 |
| Remote Ollama (MacBook) | 10 min | $0.00 | $0.00 |
| Remote Ollama (Proxmox) | 30 min | $0.00 | $0.00 |
| GPT-4o mini | 2 min | $0.007 | $0.35 |
| Claude Sonnet | 2 min | $0.17 | $8.50 |

---

## Next Steps

### Immediate: Test Quality
```bash
cd /Users/mriechers/Developer/editorial-assistant
source venv/bin/activate
python3 scripts/process_queue_auto.py
```

This will process your 4 queued Bucky projects with local Ollama.

### Review Output
```bash
# Check generated files
ls OUTPUT/2BUC0000HDDVD01/
# Should see: brainstorming.md, formatted_transcript.md, timestamp_report.md

# Compare to Claude output
diff OUTPUT/2BUC0000HD/brainstorming.md OUTPUT/2BUC0000HDDVD01/brainstorming.md
```

### If Good: Finalize
```bash
./scripts/finalize-queue.sh
# Archives transcripts, clears queue
```

### If Not Good: Try API Fallback
```bash
# Set OpenAI key
export OPENAI_API_KEY="your-key-here"

# Re-run (will auto-select cheapest available)
python3 scripts/process_queue_auto.py
```

---

## Migration Path

**Today**: Testing local Ollama on this Mac
**Next Week**: Move to spare M1 MacBook (just change endpoint)
**Future**: Move to Proxmox VM (just change endpoint again)

**Zero code changes required!**

---

## Summary

✅ **Ollama installed**: qwen2.5:14b model ready
✅ **Python scripts created**: Backend manager + queue processor
✅ **Config file ready**: Easy to migrate
✅ **Virtual environment**: Dependencies installed
✅ **System tested**: Connection working

**Ready to process your 4 queued projects at $0 cost!**

Run this when ready:
```bash
cd /Users/mriechers/Developer/editorial-assistant
source venv/bin/activate
python3 scripts/process_queue_auto.py
```
