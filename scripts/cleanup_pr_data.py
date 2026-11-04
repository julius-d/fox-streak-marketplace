#!/usr/bin/env python3
"""Clean up .foxstreak.json set files changed in a PR.

For every packs/*/sets/*.foxstreak.json file that differs from --base:
1. Regenerate the set's id and every item's id with fresh random UUIDs.
2. Remove the correct answer from an item's choices, if present there
   (choices must only hold the wrong-answer distractors).
3. Register/update the set in its pack.json (id, itemCount, updatedAt).
4. Make sure the owning pack is listed in marketplace.json.
"""

import argparse
import datetime
import json
import pathlib
import re
import subprocess
import sys
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
SET_PATH_RE = re.compile(r"^packs/[^/]+/sets/.+\.foxstreak\.json$")


def changed_set_files(base_ref: str) -> list[pathlib.Path]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACM", f"{base_ref}...HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [
        ROOT / line
        for line in result.stdout.splitlines()
        if SET_PATH_RE.match(line)
    ]


def write_json(path: pathlib.Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def clean_set_file(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text())
    data["id"] = str(uuid.uuid4())
    for item in data.get("items", []):
        item["id"] = str(uuid.uuid4())
        choices = item.get("choices")
        if choices and item["answer"] in choices:
            item["choices"] = [c for c in choices if c != item["answer"]]
    write_json(path, data)
    return data


def update_pack_json(set_path: pathlib.Path, set_data: dict) -> dict | None:
    pack_path = set_path.parent.parent / "pack.json"
    if not pack_path.exists():
        return None

    pack = json.loads(pack_path.read_text())
    rel_url = f"sets/{set_path.name}"
    today = datetime.date.today().isoformat()
    entry = next((s for s in pack["sets"] if s.get("url") == rel_url), None)

    if entry is None:
        pack["sets"].append(
            {
                "id": set_data["id"],
                "title": set_data["title"],
                "description": set_data.get("description", ""),
                "category": set_data.get("category", "vocab"),
                "itemCount": len(set_data["items"]),
                "updatedAt": today,
                "url": rel_url,
            }
        )
    else:
        entry["id"] = set_data["id"]
        entry["title"] = set_data["title"]
        entry["itemCount"] = len(set_data["items"])
        entry["updatedAt"] = today

    write_json(pack_path, pack)
    return pack


def ensure_marketplace_entry(set_path: pathlib.Path, pack_data: dict) -> None:
    marketplace_path = ROOT / "marketplace.json"
    marketplace = json.loads(marketplace_path.read_text())
    rel_url = str((set_path.parent.parent / "pack.json").relative_to(ROOT))

    if any(p.get("url") == rel_url for p in marketplace["packs"]):
        return

    marketplace["packs"].append(
        {
            "id": pack_data["id"],
            "title": pack_data["title"],
            "description": pack_data.get("description", ""),
            "url": rel_url,
        }
    )
    write_json(marketplace_path, marketplace)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="git ref to diff against, e.g. origin/main")
    args = parser.parse_args()

    set_files = changed_set_files(args.base)
    if not set_files:
        print("No changed packs/*/sets/*.foxstreak.json files found.")
        return

    for set_path in set_files:
        set_data = clean_set_file(set_path)
        pack_data = update_pack_json(set_path, set_data)
        if pack_data is not None:
            ensure_marketplace_entry(set_path, pack_data)
        print(f"Cleaned {set_path.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
