#!/usr/bin/env python3
"""
Code Buddy Status Line.
"""

import json
import os
import subprocess
import sys

# ---------- helpers ----------
def get_key(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return default
    return d if d is not None else default


def color(text: str, code: str) -> str:
    return f"{code}{text}\033[0m"


# ANSI colors
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"


# ---------- progress bar ----------
def progress_bar(percentage: float, width: int = 10) -> str:
    pct = max(0.0, min(100.0, percentage))
    filled_n = round(pct / 100.0 * width)

    bar_color = GREEN if pct < 50 else YELLOW if pct < 80 else RED
    filled = color("●" * filled_n, bar_color)
    empty = color("○" * max(0, width - filled_n), DIM)
    return f"{filled}{empty}"


# ---------- git ----------
def get_git_status(cwd: str) -> tuple[str, int, int]:
    """Return (branch_name, has_additions, has_deletions) — counts only matter for dirty check."""
    branch = ""
    added = 0
    deleted = 0

    try:
        result = subprocess.run(
            ["git", "-C", cwd, "symbolic-ref", "--short", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()

        result = subprocess.run(
            ["git", "-C", cwd, "diff", "--shortstat"],
            capture_output=True, text=True, timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            for part in result.stdout.strip().split(","):
                part = part.strip()
                if "insertion" in part:
                    added = int("".join(ch for ch in part if ch.isdigit()))
                elif "deletion" in part:
                    deleted = int("".join(ch for ch in part if ch.isdigit()))
    except Exception:
        pass

    return branch, added, deleted


# ---------- format helpers ----------
def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.2f}k"
    return str(n)


# ---------- main ----------
def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("  Code Buddy")
        return

    parts = []

    # 1. Model
    model_name = get_key(data, "model", "display_name", default="")
    if not model_name:
        model_name = os.environ.get("CODEBUDDY_MODEL", "")

    if model_name:
        model_str = "[" + color(model_name, CYAN) + color("]", DIM)
        parts.append(model_str)

    # 2. Context window usage
    cw = data.get("context_window", {}) or {}
    used_pct = cw.get("used_percentage")
    window_size = cw.get("context_window_size", 0)

    if used_pct is not None:
        pct_val = float(used_pct)
        current_usage = cw.get("current_usage") or {}
        total_input = current_usage.get("input_tokens", 0)
        token_info = f"{fmt_tokens(total_input)}/{fmt_tokens(window_size)}"

        parts.append(f"{progress_bar(pct_val)} {color(f'{pct_val:.0f}%', BOLD)} {color(token_info, DIM)}")
    elif window_size > 0:
        bar = progress_bar(0.0, width=10)
        parts.append(f"{bar} {color('0%', BOLD)} {color(f'0/{fmt_tokens(window_size)}', DIM)}")

    # 3. Git branch (cyan = clean, yellow = dirty)
    cwd = data.get("cwd") or get_key(data, "workspace", "current_dir", default="") or os.getcwd()
    branch, added, deleted = get_git_status(cwd)
    if branch:
        branch_color = YELLOW if added or deleted else CYAN
        parts.append(color(f"{branch}", branch_color))

    # Assemble
    separator = color(" │ ", DIM)
    line = separator.join(parts)

    if not line.strip():
        line = "  Code Buddy"

    print(f"  {line}\n" + color(" ", DIM), flush=True)


if __name__ == "__main__":
    main()
