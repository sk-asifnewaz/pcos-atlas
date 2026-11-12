"""Manifest integrity tests. These run without the source data, so CI is green
on a fresh clone.

    pytest -q
"""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parents[1]
MANIFEST = HERE / "manifest" / "sources.csv"


def test_manifest_exists():
    assert MANIFEST.exists(), "manifest/sources.csv is missing"


def test_one_row_per_source():
    df = pd.read_csv(MANIFEST)
    assert len(df) == 6, f"expected 6 sources, found {len(df)}"
    assert df["collection"].is_unique


def test_hashes_are_sha256():
    df = pd.read_csv(MANIFEST)
    for h in df["sha256"]:
        assert isinstance(h, str) and len(h) == 64
        int(h, 16)  # raises if not hex


def test_every_source_declares_a_licence_and_method():
    df = pd.read_csv(MANIFEST)
    assert df["licence"].notna().all()
    assert df["method"].isin(["kaggle", "dataverse", "http", "manual"]).all()
    assert df["url"].str.startswith("http").all()


def test_unlicensed_source_is_flagged():
    df = pd.read_csv(MANIFEST).set_index("collection")
    assert "unspecified" in df.loc["hasaanrana", "licence"].lower()


def test_generated_data_is_gitignored():
    """core/ holds patient rows and must never be tracked."""
    ignore = (HERE / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("core/", "sources/", "_downloads/"):
        assert pattern in ignore, f"{pattern} must be gitignored"
