# Version 2.0 Dashboard Demo Guide

This guide outlines the steps to present the **Version 2.0 Visual Dashboard** safely and effectively. It uses the `seed_demo_queue.py` script to ensure you have safe, fast-processing data to show without waiting for long jobs.

## 🛠 Preparation (Before the Demo)

1.  **Ensure Environment is Ready**:
    ```bash
    source venv/bin/activate
    ```

2.  **Seed Demo Data**:
    Run this script to inject a Short (1 min) and a Long (University Place) dummy transcript into the queue. This ensures you have immediate activity to show.
    ```bash
    python3 scripts/seed_demo_queue.py
    ```
    *Output should confirm: "Added 2 items to queue."*

## 🎬 The Demo Flow

1.  **Launch the Dashboard**:
    ```bash
    ./scripts/launch_dashboard.sh
    ```

2.  **Key Visuals to Highlight**:
    *   **Startup Speed**: Note that the "Rate" calculation now says "Calculating..." for the first minute instead of showing wild numbers.
    *   **Queue Matrix**: Show the "Pending" items from the seed script.
    *   **Processing**: Watch `DEMO_Short` pick up immediately. It's short, so it will finish quickly (showing the "Completed" state).
    *   **Cost Tracking**: Point out the "Session Cost" updating in real-time.

3.  **Controls to Demonstrate**:
    *   **Pause/Resume**: Press **`[P]`**. The border turns yellow, status shows "PAUSED". Press **`[P]`** again to resume.
    *   **Clear Completed**: Once `DEMO_Short` finishes, press **`[C]`** (now red). It will instantly remove the green "COMPLETED" row.
    *   **Error Handling (If applicable)**: If you hit a rate limit, point out that the error message is now sanitized (e.g., `Rate Limit Exceeded (429)`) instead of a giant JSON dump.

## 🧹 Cleanup (After the Demo)

1.  **Quit Dashboard**: Press **`[Q]`**.
2.  **Reset Queue** (Optional):
    If you want to run it again, just run the seed script again:
    ```bash
    python3 scripts/seed_demo_queue.py
    ```

## 📝 Talking Points regarding v2.0 status

*   **Stability**: Addressed race conditions in queue management.
*   **UX**: Improved error readability and keyboard controls.
*   **Architecture**: This dashboard represents the peak of the file-based architecture before the v3.0 database refactor.
