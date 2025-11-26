#!/usr/bin/env python3
"""
Generate cost report from processed projects
Analyzes manifest.json files to calculate total costs and token usage
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "OUTPUT"


def load_manifest(project_path: Path) -> Dict | None:
    """Load manifest.json from project directory"""
    manifest_path = project_path / "manifest.json"
    if not manifest_path.exists():
        return None

    try:
        with open(manifest_path) as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠ Error loading {manifest_path}: {e}", file=sys.stderr)
        return None


def analyze_projects() -> tuple[List[Dict], Dict]:
    """Analyze all projects and return project data and summary statistics"""
    projects = []
    total_cost = 0.0
    total_tokens = 0
    total_projects = 0
    projects_with_metrics = 0

    # Get all project directories
    for project_dir in OUTPUT_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        # Skip special directories
        if project_dir.name in ["archive", "examples", ".DS_Store"]:
            continue

        manifest = load_manifest(project_dir)
        if not manifest:
            continue

        total_projects += 1

        # Extract metrics
        project_data = {
            "name": project_dir.name,
            "status": manifest.get("status", "unknown"),
            "cost": 0.0,
            "tokens": 0,
            "deliverables": {}
        }

        # Check for processing_metrics (new format)
        if "processing_metrics" in manifest:
            project_data["cost"] = manifest["processing_metrics"].get("total_estimated_cost", 0.0)
            project_data["tokens"] = manifest["processing_metrics"].get("total_tokens", 0)
            projects_with_metrics += 1

        # Extract deliverable-level metrics
        if "deliverables" in manifest and isinstance(manifest["deliverables"], dict):
            for deliverable_type, deliverable_info in manifest["deliverables"].items():
                if deliverable_info and isinstance(deliverable_info, dict) and "metrics" in deliverable_info:
                    metrics = deliverable_info["metrics"]
                    project_data["deliverables"][deliverable_type] = {
                        "cost": metrics.get("estimated_cost", 0.0),
                        "tokens": metrics.get("total_tokens", 0),
                        "model": metrics.get("model", "unknown"),
                        "backend": metrics.get("backend", "unknown")
                    }

                    # If we don't have processing_metrics, calculate from deliverables
                    if "processing_metrics" not in manifest:
                        project_data["cost"] += metrics.get("estimated_cost", 0.0)
                        project_data["tokens"] += metrics.get("total_tokens", 0)

        if project_data["cost"] > 0 or project_data["tokens"] > 0:
            projects_with_metrics += 1

        total_cost += project_data["cost"]
        total_tokens += project_data["tokens"]
        projects.append(project_data)

    summary = {
        "total_projects": total_projects,
        "projects_with_metrics": projects_with_metrics,
        "total_cost": total_cost,
        "total_tokens": total_tokens,
        "average_cost": total_cost / projects_with_metrics if projects_with_metrics > 0 else 0.0,
        "average_tokens": total_tokens / projects_with_metrics if projects_with_metrics > 0 else 0
    }

    return projects, summary


def print_report(projects: List[Dict], summary: Dict, detailed: bool = False):
    """Print formatted cost report"""
    print("="*80)
    print("COST REPORT - Editorial Assistant Processing")
    print("="*80)
    print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n{'─'*80}")
    print("SUMMARY")
    print(f"{'─'*80}")
    print(f"Total projects analyzed: {summary['total_projects']}")
    print(f"Projects with cost metrics: {summary['projects_with_metrics']}")
    print(f"\nTotal estimated cost: ${summary['total_cost']:.4f}")
    print(f"Total tokens processed: {summary['total_tokens']:,}")
    print(f"\nAverage cost per project: ${summary['average_cost']:.4f}")
    print(f"Average tokens per project: {summary['average_tokens']:,}")

    if detailed and projects:
        # Sort by cost descending
        sorted_projects = sorted(projects, key=lambda p: p["cost"], reverse=True)

        print(f"\n{'─'*80}")
        print("PROJECT BREAKDOWN (sorted by cost)")
        print(f"{'─'*80}")

        for project in sorted_projects:
            if project["cost"] == 0 and project["tokens"] == 0:
                continue

            print(f"\n{project['name']}")
            print(f"  Status: {project['status']}")
            print(f"  Cost: ${project['cost']:.4f}")
            print(f"  Tokens: {project['tokens']:,}")

            if project["deliverables"]:
                print(f"  Deliverables:")
                for deliverable_type, metrics in project["deliverables"].items():
                    print(f"    • {deliverable_type}: ${metrics['cost']:.4f} ({metrics['tokens']:,} tokens) via {metrics['model']}")

    print(f"\n{'='*80}")


def export_csv(projects: List[Dict], output_path: Path):
    """Export cost data to CSV"""
    import csv

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Project", "Status", "Total Cost", "Total Tokens", "Brainstorming Cost",
                        "Brainstorming Tokens", "Formatter Cost", "Formatter Tokens"])

        for project in projects:
            if project["cost"] == 0 and project["tokens"] == 0:
                continue

            brainstorm = project["deliverables"].get("brainstorming", {})
            formatter = project["deliverables"].get("formatted_transcript", {})

            writer.writerow([
                project["name"],
                project["status"],
                f"${project['cost']:.4f}",
                project["tokens"],
                f"${brainstorm.get('cost', 0.0):.4f}",
                brainstorm.get("tokens", 0),
                f"${formatter.get('cost', 0.0):.4f}",
                formatter.get("tokens", 0)
            ])

    print(f"\n✓ CSV exported to: {output_path}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate cost report from processed projects")
    parser.add_argument("-d", "--detailed", action="store_true",
                       help="Show detailed breakdown by project")
    parser.add_argument("--csv", metavar="FILE",
                       help="Export data to CSV file")

    args = parser.parse_args()

    # Analyze projects
    projects, summary = analyze_projects()

    # Print report
    print_report(projects, summary, detailed=args.detailed)

    # Export CSV if requested
    if args.csv:
        csv_path = Path(args.csv)
        export_csv(projects, csv_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
