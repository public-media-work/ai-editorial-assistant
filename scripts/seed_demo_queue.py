
import json
import os
from pathlib import Path
from datetime import datetime

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
TRANSCRIPTS_DIR = PROJECT_ROOT / "transcripts"
QUEUE_FILE = PROJECT_ROOT / ".processing-requests.json"

# Demo content
DEMO_SHORT = """
00:00:00,000 --> 00:00:05,000
Welcome to this short demonstration of the PBS Wisconsin Editorial Assistant.

00:00:05,000 --> 00:00:10,000
We are testing the processing capabilities of the system.

00:00:10,000 --> 00:00:15,000
This video should be identified as a digital short because it is under one minute.

00:00:15,000 --> 00:00:20,000
The system will analyze this text and generate SEO keywords.

00:00:20,000 --> 00:00:25,000
Thank you for watching this test.
"""

DEMO_LONG = """
00:00:00,000 --> 00:00:10,000
Welcome to University Place. I am your host, and today we are discussing the history of dairy farming in Wisconsin.

00:00:10,000 --> 00:00:30,000
Dairy farming began in the mid-19th century as wheat farming declined due to soil exhaustion and the chinch bug.
Farmers needed a more sustainable alternative.

00:00:30,000 --> 00:00:50,000
William Dempster Hoard was a key figure in this transition. He promoted the idea that the cow is the foster mother of the human race.
He founded Hoard's Dairyman magazine in 1885.

00:00:50,000 --> 00:01:10,000
By 1915, Wisconsin had become the leading dairy state in the nation, producing more butter and cheese than any other state.
This identity is deeply ingrained in our culture today.

00:01:10,000 --> 00:01:30,000
We will explore the technological advancements, from the silo to the milking machine, that made this possible.
"""

def seed_demo():
    print("🌱 Seeding demo data...")
    
    # 1. Create transcript files
    short_file = TRANSCRIPTS_DIR / "DEMO_Short_ForClaude.txt"
    long_file = TRANSCRIPTS_DIR / "9UNP_Demo_ForClaude.txt" # Uses 9UNP prefix for University Place logic
    
    with open(short_file, "w") as f:
        f.write(DEMO_SHORT)
    print(f"  ✓ Created {short_file.name}")
    
    with open(long_file, "w") as f:
        f.write(DEMO_LONG)
    print(f"  ✓ Created {long_file.name}")
    
    # 2. Add to queue
    new_items = [
        {
            "project": "DEMO_Short",
            "transcript_file": short_file.name,
            "queued_at": datetime.utcnow().isoformat() + "Z",
            "status": "pending",
            "needs_brainstorming": True,
            "needs_formatting": True,
            "estimated_processing_minutes": 0.5,
            "estimated_cost": 0.001
        },
        {
            "project": "9UNP_Demo",
            "transcript_file": long_file.name,
            "queued_at": datetime.utcnow().isoformat() + "Z",
            "status": "pending",
            "needs_brainstorming": True,
            "needs_formatting": True,
            "estimated_processing_minutes": 1.5,
            "estimated_cost": 0.005
        }
    ]
    
    queue = []
    if QUEUE_FILE.exists():
        with open(QUEUE_FILE) as f:
            queue = json.load(f)
            
    # Check if they exist
    existing_projects = {item["project"] for item in queue}
    
    added_count = 0
    for item in new_items:
        if item["project"] not in existing_projects:
            queue.append(item)
            added_count += 1
            
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)
        
    print(f"  ✓ Added {added_count} items to queue.")
    print("\nReady for demo! Launch the dashboard with: ./scripts/launch_dashboard.sh")

if __name__ == "__main__":
    seed_demo()
