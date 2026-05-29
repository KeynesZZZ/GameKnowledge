#!/usr/bin/env python3
"""Unity C# staged-file rule checker for local pre-commit usage."""

from __future__ import annotations

import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


HOOK_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOK_DIR.parents[1]
CONFIG_PATH = HOOK_DIR / "config.json"


@dataclass
class Finding:
    rule_id: str
    severity: str
    title: str
    path: Path
    line: int
    code: str
    message: str
    suggestion: str
    detection: str


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        config = json.load(fh)
    rules_path = (HOOK_DIR / config["rules_source"]).resolve()
    with rules_path.open("r", encoding="utf-8") as fh:
        config["rules"] = json.load(fh)["rules"]
    return config


def staged_cs_files(config: dict) -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    files = [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]
    return filter_files(files, config)


def filter_files(files: Iterable[Path], config: dict) -> list[Path]:
    selected: list[Path] = []
    for path in files:
        normalized = path.as_posix()
        if not any(fnmatch.fnmatch(path.name, p) or fnmatch.fnmatch(normalized, p) for p in config["check_patterns"]):
            continue
        if any(fnmatch.fnmatch(normalized, p) for p in config["exclude_patterns"]):
            continue
        if (REPO_ROOT / path).exists():
            selected.append(path)
    return selected[: int(config.get("max_files", 50))]


def method_ranges(lines: list[str]) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    method_re = re.compile(r"\b(?:private|protected|public|internal)?\s*(?:void|IEnumerator)\s+(Update|FixedUpdate|LateUpdate)\s*\(")
    for index, line in enumerate(lines):
        if not method_re.search(line):
            continue
        depth = 0
        started = False
        for cursor in range(index, len(lines)):
            depth += lines[cursor].count("{")
            if "{" in lines[cursor]:
                started = True
            depth -= lines[cursor].count("}")
            if started and depth <= 0:
                ranges.append((index + 1, cursor + 1))
                break
    return ranges


def in_ranges(line_no: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= line_no <= end for start, end in ranges)


def rule_by_pattern(config: dict) -> dict[str, dict]:
    return {rule["pattern"]: rule for rule in config["rules"]}


def make_finding(rule: dict, path: Path, line_no: int, code: str) -> Finding:
    return Finding(
        rule_id=rule["id"],
        severity=rule["severity"],
        title=rule["title"],
        path=path,
        line=line_no,
        code=code.strip(),
        message=rule["message"],
        suggestion=rule["suggestion"],
        detection=rule["detection"],
    )


def analyze_file(path: Path, config: dict) -> list[Finding]:
    absolute = REPO_ROOT / path
    text = absolute.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    update_ranges = method_ranges(lines)
    rules = rule_by_pattern(config)
    findings: list[Finding] = []

    has_unsubscribe = re.search(r"(\.Unsubscribe\s*<|EventBus\.Unsubscribe\s*<|-=)", text) is not None
    has_stop_coroutine = "StopCoroutine" in text or "StopAllCoroutines" in text
    has_clear_static = ".Clear(" in text or ".Remove(" in text
    has_tween_kill = ".Kill(" in text
    has_addressables_release = "Addressables.Release" in text or ".Release(" in text

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        is_update = in_ranges(index, update_ranges)
        checks = [
            ("new_collection_in_update", is_update and re.search(r"new\s+(List|Dictionary|HashSet)\s*<", line)),
            ("get_component_in_update", is_update and "GetComponent<" in line),
            ("linq_in_update", is_update and re.search(r"\.(Where|Select|ToList|First|Any|OrderBy)\s*\(", line)),
            ("foreach_in_update", is_update and re.search(r"\bforeach\s*\(", line)),
            ("instantiate_in_update", is_update and "Instantiate(" in line),
            ("find_object_in_update", is_update and ("GameObject.Find(" in line or "FindObjectOfType" in line)),
            ("string_concat_in_update", is_update and re.search(r"\bstring\s+\w+\s*=.*\".*\"\s*\+", line)),
            ("unsafe_index_in_update", is_update and re.search(r"\w+\s*\[[^\]]+\]", line)),
            ("public_field", re.search(r"^\s*public\s+(?!class\b|struct\b|enum\b|interface\b|void\b|static\b)[\w<>\[\]]+\s+\w+\s*(=|;)", line)),
            ("resources_load", "Resources.Load" in line),
            ("singleton_instance", re.search(r"\bstatic\b.*\bInstance\b", line)),
            (
                "event_subscription_without_unsubscribe",
                ("Subscribe<" in line and not re.search(r"\bvoid\s+Subscribe\s*<", line) or "+=" in line) and not has_unsubscribe,
            ),
            ("start_coroutine_without_stop", "StartCoroutine(" in line and not has_stop_coroutine),
            ("static_collection_without_clear", re.search(r"\bstatic\b.*\b(List|Dictionary|HashSet)\s*<", line) and not has_clear_static),
            ("dotween_without_kill", re.search(r"\.DO(Move|Scale|Fade|Color|Rotate|Anchor|Punch|Shake)", line) and not has_tween_kill),
            ("addressables_without_release", "Addressables." in line and "Load" in line and not has_addressables_release),
        ]
        for pattern, matched in checks:
            if matched and pattern in rules:
                rule = rules[pattern]
                if rule["detection"] == "review" and not config.get("include_review_rules", True):
                    continue
                findings.append(make_finding(rule, path, index, stripped))
    return findings


def print_report(findings: list[Finding], files: list[Path], config: dict) -> int:
    block_on = set(config.get("block_on", ["CRITICAL"]))
    grouped: dict[str, list[Finding]] = {}
    for finding in findings:
        grouped.setdefault(finding.severity, []).append(finding)

    print("Unity code rule check")
    print(f"Checked files: {len(files)}")
    print(f"Findings: {len(findings)}")

    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        items = grouped.get(severity, [])
        if not items:
            continue
        print(f"\n{severity} ({len(items)})")
        for item in items:
            review_marker = " [review]" if item.detection == "review" else ""
            print(f"  {item.path}:{item.line} [{item.rule_id}] {item.title}{review_marker}")
            print(f"    code: {item.code}")
            print(f"    why: {item.message}")
            print(f"    fix: {item.suggestion}")

    blocked = [finding for finding in findings if finding.severity in block_on]
    if blocked:
        print("\nCommit blocked by CRITICAL findings. Use git commit --no-verify only for an intentional exception.")
        return 1

    print("\nNo blocking findings.")
    return 0


def main(argv: list[str]) -> int:
    config = load_config()
    if argv:
        files = filter_files([Path(arg) for arg in argv], config)
    else:
        files = staged_cs_files(config)
    if not files:
        print("Unity code rule check: no C# files to check.")
        return 0
    findings: list[Finding] = []
    for path in files:
        findings.extend(analyze_file(path, config))
    return print_report(findings, files, config)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
