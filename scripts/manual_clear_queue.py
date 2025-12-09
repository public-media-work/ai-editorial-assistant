
import json
from pathlib import Path

QUEUE_FILE = Path(".processing-requests.json")

def clear_completed():
    if not QUEUE_FILE.exists():
        print("No queue file found.")
        return

    with open(QUEUE_FILE) as f:
        queue = json.load(f)
    
    initial_len = len(queue)
    new_queue = [item for item in queue if item.get("status") != "completed"]
    
    if len(new_queue) < initial_len:
        with open(QUEUE_FILE, "w") as f:
            json.dump(new_queue, f, indent=2)
        print(f"Cleared {initial_len - len(new_queue)} completed projects.")
    else:
        print("No completed projects found.")

if __name__ == "__main__":
    clear_completed()
