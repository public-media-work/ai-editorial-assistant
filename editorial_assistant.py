#!/usr/bin/env python3
"""
PBS Wisconsin Editorial Assistant CLI

An ADHD-friendly command-line interface for transforming video transcripts
into SEO-optimized metadata with format consistency guarantees.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from enum import Enum


class Phase(Enum):
    """Workflow phases"""
    BRAINSTORMING = 1
    EDITING = 2
    ANALYSIS = 3
    FINALIZATION = 4


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


class Symbols:
    """Unicode symbols for visual feedback"""
    CHECK = "✓"
    ARROW = "→"
    CIRCLE = "⃝"
    WARNING = "⚠"
    ERROR = "✗"
    VIDEO = "📹"
    EDIT = "📝"
    SEARCH = "🔍"
    CLOCK = "⏱"
    PARTY = "🎉"
    LIGHTBULB = "💡"


class ProjectState:
    """Manages project state and progress tracking"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.memory = ProjectMemory(project_dir)
        self.state_file = self.memory.state_file
        self.legacy_state_file = project_dir / ".state.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load project state from JSON file"""
        self._migrate_legacy_state()
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._default_state()
        return self._default_state()

    def _default_state(self) -> Dict[str, Any]:
        """Create default project state"""
        return {
            "project_name": self.project_dir.name,
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "current_phase": Phase.BRAINSTORMING.value,
            "completed_phases": [],
            "files": {},
            "notes": [],
            "transcript_path": None,
            "program_type": None
        }

    def _migrate_legacy_state(self) -> None:
        """Move legacy .state.json into .memory/state.json when present"""
        if self.state_file.exists() or not self.legacy_state_file.exists():
            return
        try:
            with open(self.legacy_state_file, "r") as legacy_file:
                legacy_state = json.load(legacy_file)
        except (json.JSONDecodeError, OSError):
            return
        self.memory.ensure_structure()
        with open(self.state_file, "w") as target:
            json.dump(legacy_state, target, indent=2)
        try:
            self.legacy_state_file.unlink()
        except OSError:
            pass

    def save(self):
        """Save state to JSON file"""
        self.state["last_modified"] = datetime.now().isoformat()
        self.memory.ensure_structure()
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def get_progress_percentage(self) -> int:
        """Calculate completion percentage"""
        total_phases = len(Phase)
        completed = len(self.state["completed_phases"])
        return int((completed / total_phases) * 100)

    def get_current_phase(self) -> Phase:
        """Get current workflow phase"""
        return Phase(self.state["current_phase"])


class ProjectMemory:
    """Persistent shared memory structure for multi-agent coordination"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.memory_dir = project_dir / ".memory"
        self.knowledge_dir = self.memory_dir / "knowledge"
        self.handoffs_dir = self.memory_dir / "handoffs"
        self.tasks_dir = self.memory_dir / "tasks"
        self.bus_inbox_dir = self.memory_dir / "bus" / "inbox"
        self.bus_outbox_dir = self.memory_dir / "bus" / "outbox"
        self.timeline_file = self.memory_dir / "timeline.md"
        self.state_file = self.memory_dir / "state.json"
        self.ensure_structure()

    def ensure_structure(self) -> None:
        """Ensure the .memory scaffold exists"""
        directories = [
            self.memory_dir,
            self.knowledge_dir,
            self.handoffs_dir,
            self.tasks_dir,
            self.bus_inbox_dir,
            self.bus_outbox_dir,
        ]
        for path in directories:
            path.mkdir(parents=True, exist_ok=True)
        if not self.timeline_file.exists():
            self.timeline_file.write_text("# Project Timeline\n\n")

    def append_timeline(self, event: str) -> None:
        """Record a timestamped event in the timeline"""
        timestamp = datetime.now().isoformat(timespec="seconds")
        entry = f"- {timestamp}: {event}\n"
        with open(self.timeline_file, "a") as f:
            f.write(entry)

    def create_task_contract(self, task_id: str, contract: Dict[str, Any]) -> Path:
        """Write a task contract to the tasks directory"""
        self.ensure_structure()
        file_path = self.tasks_dir / f"{task_id}.yaml"
        yaml_text = self._dict_to_yaml(contract)
        file_path.write_text(yaml_text)
        return file_path

    def get_task_contracts(self) -> List[Path]:
        """List existing task contract files"""
        if not self.tasks_dir.exists():
            return []
        return sorted(self.tasks_dir.glob("*.yaml"))

    def bus(self) -> "MessageBus":
        """Convenience accessor for the message bus helper"""
        return MessageBus(self)

    def _dict_to_yaml(self, value: Any, indent: int = 0) -> str:
        lines = self._dump_yaml(value, indent)
        return "\n".join(lines) + "\n"

    def _dump_yaml(self, value: Any, indent: int) -> List[str]:
        prefix = "  " * indent
        lines: List[str] = []
        if isinstance(value, dict):
            for key, val in value.items():
                if isinstance(val, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.extend(self._dump_yaml(val, indent + 1))
                else:
                    lines.append(f"{prefix}{key}: {self._format_scalar(val)}")
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}-")
                    lines.extend(self._dump_yaml(item, indent + 1))
                else:
                    lines.append(f"{prefix}- {self._format_scalar(item)}")
        else:
            lines.append(f"{prefix}{self._format_scalar(value)}")
        return lines

    @staticmethod
    def _format_scalar(value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        text = str(value)
        if text == "" or any(char in text for char in (":", "-", "#", "{", "}", "[", "]", ",", "\n")):
            return json.dumps(text)
        return text


class MessageBus:
    """Simple filesystem-based message bus for agent hand-offs"""

    def __init__(self, memory: ProjectMemory):
        self.memory = memory
        self.memory.ensure_structure()

    def enqueue(
        self,
        direction: str,
        agent_role: str,
        payload_type: str,
        payload: Dict[str, Any],
        sender: str = "cli",
    ) -> Path:
        """Append a message to inbox or outbox"""
        if direction not in {"inbox", "outbox"}:
            raise ValueError("direction must be 'inbox' or 'outbox'")
        directory = self.memory.bus_inbox_dir if direction == "inbox" else self.memory.bus_outbox_dir
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / f"{agent_role}.jsonl"
        message = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "task_id": payload.get("task_id"),
            "from": sender,
            "to": agent_role if direction == "inbox" else "cli",
            "payload_type": payload_type,
            "payload": payload,
        }
        with open(file_path, "a") as f:
            f.write(json.dumps(message) + "\n")
        return file_path

    def read_messages(self, direction: str, agent_role: str) -> List[Dict[str, Any]]:
        """Read messages without mutating the queue"""
        if direction not in {"inbox", "outbox"}:
            raise ValueError("direction must be 'inbox' or 'outbox'")
        directory = self.memory.bus_inbox_dir if direction == "inbox" else self.memory.bus_outbox_dir
        file_path = directory / f"{agent_role}.jsonl"
        if not file_path.exists():
            return []
        messages: List[Dict[str, Any]] = []
        with open(file_path, "r") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    messages.append(json.loads(stripped))
                except json.JSONDecodeError:
                    continue
        return messages


class UI:
    """Terminal UI helper for ADHD-friendly output"""

    @staticmethod
    def box(text: str, width: int = 60) -> str:
        """Create a bordered text box"""
        top = "╭" + "─" * (width - 2) + "╮"
        bottom = "╰" + "─" * (width - 2) + "╯"
        lines = text.split("\n")
        content = "\n".join(f"│ {line:<{width - 4}} │" for line in lines)
        return f"{top}\n{content}\n{bottom}"

    @staticmethod
    def progress_bar(percentage: int, width: int = 20) -> str:
        """Create a visual progress bar"""
        filled = int((percentage / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"{bar} {percentage}%"

    @staticmethod
    def phase_indicator(current_phase: Phase, completed_phases: List[int]) -> str:
        """Visual phase progress indicator"""
        symbols = []
        names = []
        for phase in Phase:
            if phase.value in completed_phases:
                symbols.append(f"{Colors.GREEN}{Symbols.CHECK}{Colors.RESET}")
            elif phase == current_phase:
                symbols.append(f"{Colors.YELLOW}{Symbols.ARROW}{Colors.RESET}")
            else:
                symbols.append(f"{Colors.GRAY}{Symbols.CIRCLE}{Colors.RESET}")
            names.append(phase.name.capitalize())

        symbol_line = " ".join(symbols)
        name_line = " → ".join(names)
        return f"{symbol_line}\n{name_line}"

    @staticmethod
    def header(title: str, subtitle: str = "") -> str:
        """Create a prominent header"""
        content = f"  {Symbols.VIDEO}  {title}"
        if subtitle:
            content += f"\n  {subtitle}"
        return UI.box(content, width=63)


class EditorialAssistant:
    """Main CLI application"""

    def __init__(self):
        self.projects_dir = Path.home() / "editorial-assistant-projects"
        self.projects_dir.mkdir(exist_ok=True)
        self.templates_dir = Path(__file__).parent / "templates"

    def start_project(self, project_name: str):
        """Start a new video metadata project"""
        # Sanitize project name for filesystem
        safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "-"
                           for c in project_name.lower())
        project_dir = self.projects_dir / safe_name

        created_new = False
        if project_dir.exists():
            print(f"{Colors.YELLOW}Project already exists: {project_dir}{Colors.RESET}")
            response = input("Continue with existing project? [Y/n] ")
            if response.lower() == "n":
                return
        else:
            project_dir.mkdir(parents=True)
            created_new = True

        state = ProjectState(project_dir)

        # Display welcome header
        print("\n" + UI.header("PBS Wisconsin Editorial Assistant",
                               "New project created"))
        print(f"\n{Symbols.CHECK} Project folder: {project_dir}\n")

        print("I'm ready to help with this video project. I work through four phases:")
        print(f"  Phase 1: {Colors.BOLD}Research & Brainstorming{Colors.RESET} (from transcript)")
        print(f"  Phase 2: {Colors.BOLD}Editing & Revision{Colors.RESET} (from your drafts)")
        print(f"  Phase 3: {Colors.BOLD}Analysis{Colors.RESET} (SEMRush data - optional)")
        print(f"  Phase 4: {Colors.BOLD}Final deliverables{Colors.RESET}")

        print(f"\n{Colors.BOLD}To begin Phase 1, I need the video transcript.{Colors.RESET}")
        print("You can either:")
        print("  - Point me to a file: editorial-assistant transcript path/to/file.txt")
        print("  - Save transcript.txt in the project folder and run 'editorial-assistant continue'")

        print(f"\n{Symbols.LIGHTBULB} Type 'editorial-assistant status' to see progress anytime")

        # Save initial state
        state.save()
        if created_new:
            state.memory.append_timeline("Project scaffolded via CLI start command")
            state.memory.create_task_contract(
                "phase-1-brainstorming",
                {
                    "id": "phase-1-brainstorming",
                    "phase": Phase.BRAINSTORMING.value,
                    "agent_role": "brainstormer",
                    "objective": "Analyze the transcript and produce the Phase 1 brainstorming deliverable.",
                    "inputs": {
                        "required": ["transcript"],
                        "files": ["transcript.txt"],
                    },
                    "required_outputs": ["01_brainstorming.md"],
                    "handoff_to": "reviser",
                    "status": "pending",
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                },
            )

    def process_transcript(self, project_dir: Path, transcript_path: Optional[Path] = None):
        """Process transcript through Phase 1 (Brainstorming)"""
        import subprocess
        import shutil

        state = ProjectState(project_dir)

        # Find or copy transcript
        target_transcript = project_dir / "transcript.txt"

        if transcript_path:
            if not transcript_path.exists():
                print(f"{Colors.RED}{Symbols.ERROR} Transcript file not found: {transcript_path}{Colors.RESET}")
                return
            shutil.copy(transcript_path, target_transcript)
            print(f"{Symbols.CHECK} Copied transcript to project folder")
        elif not target_transcript.exists():
            print(f"{Colors.RED}{Symbols.ERROR} No transcript found.{Colors.RESET}")
            print("Either:")
            print("  - Specify a file: editorial-assistant transcript <path>")
            print(f"  - Or place transcript.txt in: {project_dir}")
            return

        # Update state
        state.state["transcript_path"] = "transcript.txt"
        state.save()

        print(f"\n{Symbols.VIDEO} Processing transcript...")
        print(f"{Symbols.CLOCK} This usually takes 30-60 seconds\n")

        # Change to project directory for the slash command
        original_dir = Path.cwd()
        os.chdir(project_dir)

        try:
            # Check if agent invocation is needed
            result = subprocess.run(
                ["python3", str(Path(__file__).parent / "editorial_assistant.py"), "brainstorm-internal"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 99:
                # Agent invocation required
                # For MVP: provide clear instructions
                # In production: this would use Task tool automatically
                print(f"\n{Colors.YELLOW}Agent processing step:{Colors.RESET}\n")
                print("The video-metadata-seo-editor agent will now analyze your transcript.")
                print(f"Project directory: {Colors.BLUE}{project_dir}{Colors.RESET}\n")

                # The actual invocation would happen here
                # For now, let's create a demonstration workflow
                print(f"{Symbols.LIGHTBULB} To complete this step manually:")
                print(f"  1. cd {project_dir}")
                print(f"  2. Run: claude chat (or use Claude Code)")
                print(f"  3. Use the /brainstorm command")
                print(f"  4. The agent will create: 01_brainstorming.md")
                print("\nOnce complete, run:")
                print(f"  editorial-assistant status\n")
                return

            elif result.returncode != 0:
                print(f"{Colors.RED}{Symbols.ERROR} Processing failed:{Colors.RESET}")
                print(result.stderr)
                return

        finally:
            os.chdir(original_dir)

        # Check if output was created
        output_file = project_dir / "01_brainstorming.md"
        if output_file.exists():
            # Success! Update state
            state.state["completed_phases"].append(Phase.BRAINSTORMING.value)
            state.state["current_phase"] = Phase.EDITING.value
            state.memory.append_timeline("Phase 1 (Brainstorming) completed")
            state.save()

            # Display celebration
            print(UI.celebration("Phase 1 Complete: Brainstorming"))
            print(f"Progress: {UI.progress_bar(state.get_progress_percentage())}\n")
            print(f"{Symbols.CHECK} Brainstorming document created")
            print(f"  {Colors.BLUE}→ {output_file}{Colors.RESET}\n")

            # Show what was generated
            print("Generated:")
            print("  • Title options (multiple lengths)")
            print("  • Short descriptions")
            print("  • Long descriptions")
            print("  • 20 SEO keywords")
            print("  • Notable quotes")

            print(f"\n{Colors.BOLD}Next step: Phase 2 - Editing & Revision{Colors.RESET}")
            print("  Provide your draft copy (text or screenshot) for review.\n")

            print(f"{Symbols.LIGHTBULB} Use 'editorial-assistant preview' to view the brainstorming document")
            print(f"{Symbols.LIGHTBULB} Use 'editorial-assistant revise' when ready for Phase 2")
        else:
            print(f"{Colors.RED}{Symbols.ERROR} Output file was not created{Colors.RESET}")

    def find_active_projects(self) -> List[Path]:
        """Find all projects sorted by recent activity"""
        projects = []
        for item in self.projects_dir.iterdir():
            if item.is_dir():
                state_file = item / ".memory" / "state.json"
                if state_file.exists():
                    projects.append(item)

        # Sort by last modified
        def get_last_modified(p: Path) -> str:
            state = ProjectState(p)
            return state.state.get("last_modified", "")

        projects.sort(key=get_last_modified, reverse=True)
        return projects

    def show_status(self, project_dir: Path):
        """Display project status with ADHD-friendly formatting"""
        state = ProjectState(project_dir)

        print("\n" + UI.header(state.state["project_name"]))

        print(f"\nProgress: {UI.progress_bar(state.get_progress_percentage())}")
        print()
        print(UI.phase_indicator(state.get_current_phase(),
                                 state.state["completed_phases"]))

        print(f"\n{Symbols.LIGHTBULB} Use 'editorial-assistant continue' to resume work")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="PBS Wisconsin Editorial Assistant - Video Metadata CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start a new project")
    start_parser.add_argument("name", nargs="?", help="Project name")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show project status")
    status_parser.add_argument("project", nargs="?", help="Project directory")

    # Transcript command
    transcript_parser = subparsers.add_parser("transcript", help="Process transcript (Phase 1)")
    transcript_parser.add_argument("file", nargs="?", help="Path to transcript file")
    transcript_parser.add_argument("--project", help="Project directory (defaults to most recent)")

    # Internal command for agent processing (not shown in help)
    brainstorm_parser = subparsers.add_parser("brainstorm-internal", add_help=False)

    args = parser.parse_args()

    app = EditorialAssistant()

    if args.command == "start":
        if args.name:
            app.start_project(args.name)
        else:
            print("Usage: editorial-assistant start <project-name>")
            print('Example: editorial-assistant start "Here and Now Interview"')
    elif args.command == "status":
        if args.project:
            app.show_status(Path(args.project))
        else:
            print("Please specify a project directory")
    elif args.command == "transcript":
        # Find project directory
        if hasattr(args, "project") and args.project:
            project_dir = Path(args.project)
        else:
            # Use most recent project
            projects = app.find_active_projects()
            if not projects:
                print(f"{Colors.RED}No active projects found.{Colors.RESET}")
                print("Create one first: editorial-assistant start <name>")
                return
            project_dir = projects[0]

        # Process transcript
        transcript_path = Path(args.file) if args.file else None
        app.process_transcript(project_dir, transcript_path)

    elif args.command == "brainstorm-internal":
        # This is called internally by process_transcript
        # Running in project directory where transcript.txt exists
        # Signal to parent that agent invocation is needed
        print("AGENT_INVOCATION_REQUIRED")
        sys.exit(99)  # Special exit code to signal agent needed

    else:
        # No command - show help
        parser.print_help()


if __name__ == "__main__":
    main()
