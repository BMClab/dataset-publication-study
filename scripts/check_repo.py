"""Check the repository's archived evidence and documents.

Usage, from the repository root: python scripts/check_repo.py

Uses only the standard library. It verifies that:
- every file in evidence/provenance.json exists and matches its distributed SHA-256;
- every local Markdown link resolves, including #anchors in Markdown files;
- the archived table renderer reproduces the tables published in the matched report.
Exits with status 1 and lists each problem when any check fails.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "evidence/reports/lab_format_benchmark.md"


def check_provenance():
    manifest = json.loads((ROOT / "evidence/provenance.json").read_text())
    problems = []
    for entry in manifest["files"]:
        path = ROOT / entry["file"]
        if not path.is_file():
            problems.append(f"provenance: missing {entry['file']}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            problems.append(f"provenance: SHA-256 differs for {entry['file']}")
    return problems, f"{len(manifest['files'])} provenance hashes"


def heading_anchor(text):
    text = re.sub(r"<[^>]+>", "", text.strip().lower()).replace("`", "").replace("*", "")
    return "".join(c for c in text if c.isalnum() or c in " -_").replace(" ", "-")


def anchors(path):
    found, seen, in_code = set(), {}, False
    for line in path.read_text().splitlines():
        if line.startswith("```"):
            in_code = not in_code
        match = None if in_code else re.match(r"#{1,6}\s+(.*)", line)
        if match:
            anchor = heading_anchor(match.group(1))
            count = seen.get(anchor, 0)
            seen[anchor] = count + 1
            found.add(anchor if count == 0 else f"{anchor}-{count}")
    return found


def tracked_markdown():
    listed = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [ROOT / name for name in listed.stdout.split()]


def check_links():
    problems, count, cache = [], 0, {}
    for document in tracked_markdown():
        for target in re.findall(r"\]\(([^)\s]+)\)", document.read_text()):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            count += 1
            path, _, fragment = target.partition("#")
            resolved = (document.parent / path).resolve() if path else document
            name = document.relative_to(ROOT)
            if not resolved.exists():
                problems.append(f"link: {name} -> {target} (missing file)")
            elif fragment and resolved.suffix == ".md":
                if resolved not in cache:
                    cache[resolved] = anchors(resolved)
                if fragment not in cache[resolved]:
                    problems.append(f"link: {name} -> {target} (missing anchor)")
    return problems, f"{count} local links"


def check_tables():
    rendered = subprocess.run(
        [sys.executable, "evidence/methods/lab_format_tables.py", "evidence/observations"],
        cwd=ROOT, capture_output=True, text=True)
    if rendered.returncode:
        return [f"tables: renderer failed: {rendered.stderr.strip()}"], "archived tables"
    report = REPORT.read_text()
    lines = [line for line in rendered.stdout.splitlines() if line.strip()]
    problems = [f"tables: rendered line not in report: {line}" for line in lines if line not in report]
    return problems, f"{len(lines)} rendered table lines"


def main():
    failures = []
    for check in (check_provenance, check_links, check_tables):
        problems, scope = check()
        print(f"{'FAIL' if problems else 'ok  '} {scope}")
        failures.extend(problems)
    for problem in failures:
        print(f"  {problem}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
