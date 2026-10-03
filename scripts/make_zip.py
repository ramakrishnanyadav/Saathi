"""Packaging script to create clean saath-project.zip archive."""

from __future__ import annotations

import os
import zipfile

IGNORED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    "node_modules",
}

IGNORED_EXTS = {".zip", ".db", ".db-wal", ".db-shm"}


def create_zip(output_path: str = "saath-project.zip") -> None:
    count = 0
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for f in files:
                ext = os.path.splitext(f)[1]
                if ext in IGNORED_EXTS:
                    continue
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, ".")
                z.write(full_path, rel_path)
                count += 1
    print(f"Created {output_path} successfully containing {count} files.")


if __name__ == "__main__":
    create_zip()
