"""Scan real open-source projects to prove PyPerfOptimizer finds real issues."""

import glob
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyperfoptimizer.autofix import scan_file


def scan_project(name: str, pattern: str, max_files: int = 50):
    """Scan a project and return results."""
    files = sorted(glob.glob(pattern, recursive=True))[:max_files]
    all_opts = []
    for f in files:
        try:
            opts = scan_file(f)
            for o in opts:
                o.file = f  # attach filename
            all_opts.extend(opts)
        except Exception:
            pass  # skip unparseable files
    return all_opts


def main():
    projects = {
        "FastAPI": "/tmp/fastapi/fastapi/**/*.py",
        "Flask": "/tmp/flask/src/flask/**/*.py",
        "Django (utils)": "/tmp/django/django/utils/**/*.py",
    }

    all_results = {}
    lines = []
    lines.append("=" * 70)
    lines.append("PyPerfOptimizer — Real-World Project Scan Results")
    lines.append("=" * 70)
    lines.append("")

    grand_total = 0
    grand_patterns = Counter()

    for project, pattern in projects.items():
        opts = scan_project(project, pattern)
        all_results[project] = opts
        grand_total += len(opts)

        patterns = Counter(o.pattern_name for o in opts)
        grand_patterns.update(patterns)

        lines.append(f"## {project}: {len(opts)} optimizations found")
        files_scanned = len(sorted(glob.glob(pattern, recursive=True))[:50])
        lines.append(f"   Files scanned: {files_scanned}")
        lines.append(f"   Breakdown by pattern:")
        for pat, count in patterns.most_common():
            lines.append(f"     - {pat}: {count}")
        lines.append("")

    # Summary
    lines.append("=" * 70)
    lines.append(f"TOTAL: {grand_total} optimizations across {len(projects)} projects")
    lines.append("=" * 70)
    lines.append("")
    lines.append("## Pattern Breakdown (all projects)")
    for pat, count in grand_patterns.most_common():
        lines.append(f"  {pat}: {count}")
    lines.append("")

    # Top 5 most impactful (diverse — best from each pattern)
    all_opts = []
    for opts in all_results.values():
        all_opts.extend(opts)

    def speedup_key(o):
        try:
            # Handle "10-1000x for recursive functions", "2-10x", "1.2x"
            s = o.expected_speedup.lower().split("x")[0].strip()
            if "-" in s:
                return float(s.split("-")[-1])
            return float(s)
        except (ValueError, AttributeError):
            return 0.0

    all_opts.sort(key=speedup_key, reverse=True)

    lines.append("## Top 5 Most Impactful Findings (by expected speedup)")
    lines.append("")
    seen_patterns = set()
    shown = 0
    for o in all_opts:
        if o.pattern_name in seen_patterns:
            continue
        seen_patterns.add(o.pattern_name)
        shown += 1
        rel_path = o.file.replace("/tmp/", "")
        lines.append(f"  {shown}. [{o.expected_speedup}] {o.pattern_name}")
        lines.append(f"     File: {rel_path}:{o.line}")
        lines.append(f"     {o.description}")
        if o.original_code:
            code_preview = o.original_code.strip().split("\n")[0][:80]
            lines.append(f"     Code: {code_preview}")
        lines.append("")
        if shown >= 7:
            break

    output = "\n".join(lines)
    print(output)

    # Save
    out_path = Path(__file__).parent / "real_world_scan.txt"
    out_path.write_text(output)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
