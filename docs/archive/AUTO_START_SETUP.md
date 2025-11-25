# Auto-Start Transcript Watcher

The transcript watcher is now configured to start automatically when you log in to your Mac.

---

## ✅ Current Status

**Watcher**: Running (PID shown in logs)
**Auto-start**: Enabled (loads at login)
**Logs**: `/Users/mriechers/Developer/editorial-assistant/logs/`

---

## How It Works

### LaunchAgent Configuration

macOS LaunchAgent file created at:
```
~/Library/LaunchAgents/com.editorial-assistant.transcript-watcher.plist
```

This tells macOS to:
- Start the watcher when you log in
- Keep it running (restart if it crashes)
- Log output to files for monitoring

### What Happens at Login

1. You log in to your Mac
2. LaunchAgent automatically starts the watcher
3. Watcher monitors `/transcripts/` folder every 10 seconds
4. New transcripts are automatically detected and set up
5. Runs until you log out or manually stop it

---

## Managing the Watcher

### Check Status
```bash
# See if watcher is running
launchctl list | grep editorial-assistant
# Output shows: [PID] [exit code] [name]
# Example: 29390	0	com.editorial-assistant.transcript-watcher
```

### View Logs
```bash
# See what the watcher is doing
tail -f logs/watcher.log

# See any errors
tail -f logs/watcher.error.log
```

### Stop the Watcher
```bash
# Stop temporarily (will restart at next login)
launchctl stop com.editorial-assistant.transcript-watcher

# Stop and disable auto-start
launchctl unload ~/Library/LaunchAgents/com.editorial-assistant.transcript-watcher.plist
```

### Start the Watcher Manually
```bash
# If you stopped it and want to restart
launchctl start com.editorial-assistant.transcript-watcher

# Or reload the agent
launchctl load ~/Library/LaunchAgents/com.editorial-assistant.transcript-watcher.plist
```

### Restart the Watcher
```bash
# Useful after updating scripts
launchctl stop com.editorial-assistant.transcript-watcher
launchctl start com.editorial-assistant.transcript-watcher

# Or use restart
launchctl kickstart -k gui/$(id -u)/com.editorial-assistant.transcript-watcher
```

---

## Configuration

### Change Check Interval

Edit the plist file:
```bash
# Open in editor
nano ~/Library/LaunchAgents/com.editorial-assistant.transcript-watcher.plist
```

Find this section:
```xml
<key>ProgramArguments</key>
<array>
    <string>/Users/mriechers/Developer/editorial-assistant/scripts/watch-transcripts.sh</string>
    <string>--interval</string>
    <string>10</string>  <!-- Change this number -->
</array>
```

Change `<string>10</string>` to your desired interval in seconds.

Then reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.editorial-assistant.transcript-watcher.plist
launchctl load ~/Library/LaunchAgents/com.editorial-assistant.transcript-watcher.plist
```

### Disable Auto-Start

If you want to run the watcher manually instead:

```bash
# Disable auto-start
launchctl unload ~/Library/LaunchAgents/com.editorial-assistant.transcript-watcher.plist

# Optionally, remove the plist file
rm ~/Library/LaunchAgents/com.editorial-assistant.transcript-watcher.plist
```

To run manually when needed:
```bash
./scripts/watch-transcripts.sh
```

---

## Log Files

### Location
```
editorial-assistant/logs/
├── watcher.log        # Standard output (what you'd see in terminal)
└── watcher.error.log  # Error output (if something goes wrong)
```

### View Live Activity
```bash
# Follow the log in real-time
tail -f logs/watcher.log
```

You'll see:
- Startup message
- New file detections
- Batch setup confirmations
- Any processing status

### Example Log Output
```
╔════════════════════════════════════════════════════════╗
║   Editorial Assistant - Transcript Folder Watcher     ║
╚════════════════════════════════════════════════════════╝

Watching: /Users/mriechers/Developer/editorial-assistant/transcripts
Check interval: 10s
State file: .watch-state

✓ Watcher started (PID: 29390)

▶ New transcript detected: 9UNP2007HD_ForClaude.txt
  → Running batch setup...
  ✓ Project setup complete: 9UNP2007HD
  → Ready for agent processing
```

### Log Rotation

Logs will grow over time. To manage:

```bash
# View log size
ls -lh logs/

# Clear logs
> logs/watcher.log
> logs/watcher.error.log

# Or delete and restart watcher (will recreate)
rm logs/*.log
launchctl stop com.editorial-assistant.transcript-watcher
launchctl start com.editorial-assistant.transcript-watcher
```

---

## Troubleshooting

### Watcher Not Running After Login

**Check if loaded**:
```bash
launchctl list | grep editorial-assistant
# Should show the process
```

**If not listed**:
```bash
# Load it manually
launchctl load ~/Library/LaunchAgents/com.editorial-assistant.transcript-watcher.plist
```

**Check for errors**:
```bash
cat logs/watcher.error.log
```

### Files Not Being Detected

**Check watcher status**:
```bash
launchctl list | grep editorial-assistant
# Look for exit code (middle number)
# 0 = running normally
# Non-zero = crashed or error
```

**View recent activity**:
```bash
tail -30 logs/watcher.log
```

**Verify script is executable**:
```bash
ls -la scripts/watch-transcripts.sh
# Should show: -rwxr-xr-x (x = executable)
```

### Watcher Keeps Crashing

**Check error log**:
```bash
cat logs/watcher.error.log
```

**Common issues**:
- Script permissions: `chmod +x scripts/watch-transcripts.sh`
- Path issues: Verify paths in plist file are absolute
- Dependency missing: Check batch script works manually

**Test manually first**:
```bash
# Stop the LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.editorial-assistant.transcript-watcher.plist

# Run manually to see errors
./scripts/watch-transcripts.sh
```

---

## Best Practices

### 1. Check Logs Periodically
```bash
# Quick check if it's working
tail -20 logs/watcher.log
```

### 2. Clear State After Archiving
```bash
# After running archive script
./scripts/archive-processed-transcripts.sh

# Clear state (archived files won't be detected anyway)
rm .watch-state
```

### 3. Monitor for Stuck Processes
```bash
# See if watcher is responding
ps aux | grep watch-transcripts

# If frozen, restart
launchctl kickstart -k gui/$(id -u)/com.editorial-assistant.transcript-watcher
```

### 4. Update Scripts Safely
```bash
# When updating watch-transcripts.sh
launchctl stop com.editorial-assistant.transcript-watcher
# Make your changes
launchctl start com.editorial-assistant.transcript-watcher
```

---

## Complete Workflow

### Daily Routine

**Morning**:
1. Log in to your Mac (watcher starts automatically)
2. Drop transcripts into `/transcripts/` folder
3. Watcher detects and sets them up within 10 seconds

**During the day**:
4. Process projects with agents when convenient
5. Edit in Claude Desktop via MCP
6. Save revisions

**End of day**:
7. Run archive script to clean up
```bash
./scripts/archive-processed-transcripts.sh
```

### No Manual Intervention Needed

The watcher runs silently in the background:
- ✅ Starts at login automatically
- ✅ Monitors folder continuously
- ✅ Creates project structure on detection
- ✅ Logs activity for your review
- ✅ Keeps running until logout

---

## Uninstall

If you want to remove the auto-start:

```bash
# Stop and unload
launchctl unload ~/Library/LaunchAgents/com.editorial-assistant.transcript-watcher.plist

# Remove plist file
rm ~/Library/LaunchAgents/com.editorial-assistant.transcript-watcher.plist

# Optionally remove logs
rm -rf logs/
```

The script itself (`watch-transcripts.sh`) will still work manually if needed.

---

## Summary

**Status**: ✅ Auto-start enabled
**Runs**: At login, continuously
**Monitors**: `/transcripts/` folder every 10 seconds
**Logs**: `logs/watcher.log` and `logs/watcher.error.log`

**Commands**:
- View status: `launchctl list | grep editorial-assistant`
- View logs: `tail -f logs/watcher.log`
- Stop: `launchctl stop com.editorial-assistant.transcript-watcher`
- Start: `launchctl start com.editorial-assistant.transcript-watcher`
- Disable: `launchctl unload ~/Library/LaunchAgents/com.editorial-assistant.transcript-watcher.plist`

**Your workflow is now fully automated** - just drop files and they'll be ready for processing! 🎉
