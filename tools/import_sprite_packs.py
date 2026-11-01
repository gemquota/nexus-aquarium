#!/usr/bin/env python3
"""Safely stage locally downloaded sprite ZIPs without committing licensed binaries.

Example:
  python3 tools/import_sprite_packs.py asset_staging/fathom-underwater.zip --pack fathom-underwater

The staged files live under local_assets/ (gitignored by design).
"""
from __future__ import annotations

import argparse
import json
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "local_assets" / "sprites"
IMAGE_SUFFIXES = {".png", ".webp", ".gif", ".jpg", ".jpeg", ".svg"}
META_SUFFIXES = {".json", ".txt", ".md", ".gpl", ".ase", ".aseprite", ".csv", ".xml"}
MAX_FILES = 12000
MAX_MEMBER_BYTES = 80 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024


def safe_member(info: zipfile.ZipInfo) -> PurePosixPath | None:
    name = info.filename.replace("\\", "/")
    path = PurePosixPath(name)
    mode = info.external_attr >> 16
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        return None
    if stat.S_ISLNK(mode) or info.is_dir():
        return None
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--pack", required=True, help="ID from assets/sprites/sources.json")
    args = parser.parse_args()

    archive = args.archive if args.archive.is_absolute() else ROOT / args.archive
    if not archive.is_file() or archive.suffix.lower() != ".zip":
        parser.error("archive must be an existing .zip file")
    if not args.pack.replace("-", "").replace("_", "").isalnum():
        parser.error("pack ID may contain only letters, numbers, hyphens and underscores")

    target = OUTPUT / args.pack
    target.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, object]] = []
    total = 0

    with zipfile.ZipFile(archive) as zf:
        infos = zf.infolist()
        if len(infos) > MAX_FILES:
            raise SystemExit(f"Archive contains too many entries ({len(infos)} > {MAX_FILES})")
        for info in infos:
            rel = safe_member(info)
            if rel is None:
                continue
            suffix = Path(rel.name).suffix.lower()
            if suffix not in IMAGE_SUFFIXES | META_SUFFIXES:
                continue
            if info.file_size > MAX_MEMBER_BYTES:
                raise SystemExit(f"Refusing oversized member: {info.filename}")
            total += info.file_size
            if total > MAX_TOTAL_BYTES:
                raise SystemExit("Archive expands beyond the 1 GiB safety limit")
            destination = target.joinpath(*rel.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, destination.open("wb") as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)
            files.append({
                "path": destination.relative_to(ROOT).as_posix(),
                "source_path": rel.as_posix(),
                "bytes": info.file_size,
                "type": "image" if suffix in IMAGE_SUFFIXES else "metadata"
            })

    manifest_path = OUTPUT / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    current = {}
    if manifest_path.exists():
        try:
            current = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            current = {}
    current.setdefault("schema_version", 1)
    current.setdefault("projection", "side_view")
    current.setdefault("packs", {})
    current["packs"][args.pack] = {
        "archive": archive.name,
        "imported_files": files,
        "image_count": sum(item["type"] == "image" for item in files),
        "metadata_count": sum(item["type"] == "metadata" for item in files)
    }
    manifest_path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(files)} files ({current['packs'][args.pack]['image_count']} images) to {target}")
    print(f"Local manifest: {manifest_path}")
    print("These files remain local and are not added to Git.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
