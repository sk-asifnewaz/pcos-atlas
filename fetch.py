#!/usr/bin/env python
"""
fetch.py - retrieve the five source datasets and verify them against
manifest/sources.csv.

The corpus is not redistributed. This script reconstructs it from the
original publishers, then checks every file against a recorded SHA-256.
If a publisher silently updates a dataset, the hash will not match and the
build will stop rather than produce a different corpus.

Usage
-----
    python fetch.py --verify          # check what is already present
    python fetch.py                   # download what is missing, then verify
    python fetch.py --from-dir PATH   # use files already downloaded elsewhere
    python fetch.py --list            # show sources, licences, methods

Requirements
------------
    Kaggle sources need the Kaggle CLI and credentials:
        pip install kaggle
        # ~/.kaggle/kaggle.json  (Account -> Create New API Token)
    Dataverse and direct sources need only network access.

Exit codes
----------
    0  every source present and hash-verified
    1  at least one source missing, unreadable or changed
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest" / "sources.csv"
SOURCES = HERE / "sources"
DOWNLOADS = HERE / "_downloads"

DATAVERSE_API = "https://dataverse.harvard.edu/api"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path: Path, expected: str) -> bool:
    return path.exists() and sha256(path) == expected


def find_by_hash(root: Path, expected: str) -> Path | None:
    """Locate a file by content, not by name.

    Publishers rename files between releases; a hash match is the only
    reliable identity test.
    """
    for p in root.rglob("*"):
        if p.is_file() and p.stat().st_size > 0:
            try:
                if sha256(p) == expected:
                    return p
            except OSError:
                continue
    return None


def unzip_all(archive: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        z.extractall(dest)


# --------------------------------------------------------------------------
# fetchers
# --------------------------------------------------------------------------

def fetch_kaggle(locator: str, dest: Path) -> None:
    if shutil.which("kaggle") is None:
        raise RuntimeError(
            "Kaggle CLI not found. Install with `pip install kaggle` and place "
            "kaggle.json in ~/.kaggle/ (Kaggle > Account > Create New API Token)."
        )
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["kaggle", "datasets", "download", "-d", locator, "-p", str(dest), "--unzip"],
        check=True,
    )


def fetch_dataverse(locator: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    meta_url = f"{DATAVERSE_API}/datasets/:persistentId/?persistentId={locator}"
    with urllib.request.urlopen(meta_url, timeout=60) as r:
        meta = json.load(r)
    files = meta["data"]["latestVersion"]["files"]
    if not files:
        raise RuntimeError(f"No files listed for {locator}")
    for entry in files:
        fid = entry["dataFile"]["id"]
        name = entry["dataFile"].get("filename", f"file_{fid}")
        out = dest / name
        with urllib.request.urlopen(
            f"{DATAVERSE_API}/access/datafile/{fid}", timeout=120
        ) as r, open(out, "wb") as f:
            shutil.copyfileobj(r, f)


def fetch_http(url: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    name = url.rstrip("/").split("/")[-1] or "download"
    with urllib.request.urlopen(url, timeout=120) as r, open(dest / name, "wb") as f:
        shutil.copyfileobj(r, f)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def load_manifest() -> pd.DataFrame:
    if not MANIFEST.exists():
        sys.exit(f"manifest not found: {MANIFEST}")
    return pd.read_csv(MANIFEST)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true",
                    help="only check files already present; never download")
    ap.add_argument("--from-dir", type=Path, default=None,
                    help="directory containing manually downloaded source files")
    ap.add_argument("--list", action="store_true", help="list sources and exit")
    args = ap.parse_args()

    man = load_manifest()

    if args.list:
        for _, r in man.iterrows():
            print(f"{r['collection']:<18} {r['method']:<10} {r['licence']:<18} {r['url']}")
        return 0

    SOURCES.mkdir(exist_ok=True)
    failures: list[str] = []

    for _, r in man.iterrows():
        name = r["collection"]
        ext = Path(r["filename"]).suffix
        target = SOURCES / f"{name}{ext}"

        # already present and correct?
        if verify(target, r["sha256"]):
            print(f"[ok]      {name}: {target.name} (hash verified)")
            continue

        if args.verify:
            print(f"[MISSING] {name}: expected {target.name} with sha256 {r['sha256'][:16]}...")
            failures.append(name)
            continue

        # manual drop-in directory
        if args.from_dir:
            hit = find_by_hash(args.from_dir, r["sha256"])
            if hit:
                shutil.copy2(hit, target)
                print(f"[copied]  {name}: {hit.name} -> {target.name}")
                continue
            print(f"[MISSING] {name}: no file in {args.from_dir} matches the recorded hash")
            failures.append(name)
            continue

        # download
        work = DOWNLOADS / name
        try:
            if r["method"] == "kaggle":
                fetch_kaggle(r["locator"], work)
            elif r["method"] == "dataverse":
                fetch_dataverse(r["locator"], work)
            elif r["method"] == "http":
                fetch_http(r["locator"] or r["url"], work)
            else:
                print(f"[manual]  {name}: {r['notes']}\n          {r['url']}")
                failures.append(name)
                continue
        except Exception as e:  # noqa: BLE001 - report and continue
            print(f"[error]   {name}: {e}")
            failures.append(name)
            continue

        hit = find_by_hash(work, r["sha256"])
        if hit is None:
            print(f"[CHANGED] {name}: downloaded files do not match the recorded hash.")
            print(f"          expected sha256 {r['sha256']}")
            print(f"          The publisher may have updated the dataset. Do not build "
                  f"until this is resolved.")
            failures.append(name)
            continue

        shutil.copy2(hit, target)
        print(f"[fetched] {name}: {hit.name} -> {target.name} (hash verified)")

    if failures:
        print(f"\n{len(failures)} source(s) unresolved: {', '.join(failures)}")
        print("Re-run with --from-dir pointing at manually downloaded files.")
        return 1

    print(f"\nAll {len(man)} sources present and hash-verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
