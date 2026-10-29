"""Export pip compatibility files from uv.lock, or verify them with --check.

Edit pyproject.toml, run uv lock, then this script. Never edit generated files.
"""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    mismatches = []
    for filename, groups in (("requirements.txt", ["--no-dev"]), ("requirements-dev.txt", [])):
        command = ["uv", "export", "--locked", "--no-emit-project", "--no-hashes",
                   "--no-header", "--no-annotate", "--format", "requirements-txt", *groups]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            print("ERROR: uv export failed. Run uv lock and check pyproject.toml/uv.lock.")
            return 2
        path = ROOT / "backend" / filename
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != result.stdout:
                mismatches.append(filename)
        else:
            path.write_text(result.stdout, encoding="utf-8", newline="\n")
    if mismatches:
        print("ERROR: generated requirements are stale: " + ", ".join(mismatches))
        print("Run: uv run --locked python utils/scripts/sync_requirements.py")
        return 1
    print("Requirements match uv.lock." if args.check else "Generated runtime and development requirements from uv.lock.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
