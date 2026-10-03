"""Packages the SAATH project cleanly into saath-project.zip, excluding temp caches."""

import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ZIP = ROOT / "saath-project.zip"

EXCLUDE_DIRS = {
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".hypothesis",
    ".mypy_cache",
    ".ruff_cache",
    ".git",
}

EXCLUDE_FILES = {
    "saath.db",
    "saath.db-shm",
    "saath.db-wal",
    "saath-project.zip",
}


def package():
    count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.endswith(".egg-info")]
            for file in files:
                if file in EXCLUDE_FILES or file.endswith(".pyc"):
                    continue
                full_path = Path(root) / file
                arcname = full_path.relative_to(ROOT)
                zf.write(full_path, arcname)
                count += 1
    print(f"Successfully packaged {count} files into {OUTPUT_ZIP} ({OUTPUT_ZIP.stat().st_size} bytes)")


if __name__ == "__main__":
    package()
