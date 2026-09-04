#!/usr/bin/env python3
"""
Install the Code Buddy status line:
  1. Copy statusline.py to ~/.codebuddy/statusline.py
  2. Merge the JSON below into ~/.codebuddy/settings.json
"""

import json
import os
import shutil

SETTINGS_OVERRIDE = {
    "statusLine": {
        "type": "command",
        "command": "python3 statusline.py",
        "padding": 0
    }
}


def main():
    codebuddy_dir = os.path.expanduser("~/.codebuddy")
    os.makedirs(codebuddy_dir, exist_ok=True)

    statusline_dst = os.path.join(codebuddy_dir, "statusline.py")
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "statusline.py")
    shutil.copy2(src, statusline_dst)
    print(f"Copied statusline.py -> {statusline_dst}")

    settings_path = os.path.join(codebuddy_dir, "settings.json")
    settings = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except (json.JSONDecodeError, OSError):
            settings = {}

    def deep_merge(base, override):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                deep_merge(base[k], v)
            else:
                base[k] = v

    deep_merge(settings, SETTINGS_OVERRIDE)

    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Updated settings: {settings_path}")
    print("Done. Restart Code Buddy to apply the status line.")


if __name__ == "__main__":
    main()
