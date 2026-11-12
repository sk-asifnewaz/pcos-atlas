"""Build manifest/sources.csv: one row per source file, with SHA-256 and a
retrieval method. fetch.py consumes this file directly.
"""
import hashlib
from datetime import date
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
TAB = HERE.parent / "Tabular" / "Tabular Datasets"
MAN = HERE / "manifest"
MAN.mkdir(exist_ok=True)

# collection, prefix, must-contain, ext, sheet, licence, url, method, slug/doi, note
SOURCES = [
    ("Kottarathil_full", "4.", "without_infertility", ".xlsx", "Full_new",
     "CC BY-NC-SA 4.0",
     "https://www.kaggle.com/datasets/prasoonkottarathil/polycystic-ovary-syndrome-pcos",
     "kaggle", "prasoonkottarathil/polycystic-ovary-syndrome-pcos",
     "Download the 'without infertility' workbook, not the 3-column subset."),
    ("Chaabouni", "9.", None, ".xlsx", "vitD09_02_18donnees.spv",
     "CC BY 4.0",
     "https://data.mendeley.com/datasets/tw34c7hv7z/1",
     "manual", "",
     "Mendeley serves files through a per-file UUID; download manually and pass --from-dir."),
    ("Gawron", "16.", None, ".xlsx", "Sheet1",
     "CC0 1.0",
     "https://doi.org/10.7910/DVN/CSU6WA",
     "dataverse", "doi:10.7910/DVN/CSU6WA",
     "Harvard Dataverse dataset."),
    ("Sahil_Koli", "6.", None, ".csv", None,
     "CC0",
     "https://www.kaggle.com/datasets/sahilkoli04/pcos2023",
     "kaggle", "sahilkoli04/pcos2023",
     ""),
    ("hasaanrana", "5.", None, ".csv", None,
     "unspecified",
     "https://www.kaggle.com/datasets/hasaanrana/diet-exercise-and-pcos-insights",
     "kaggle", "hasaanrana/diet-exercise-and-pcos-insights",
     "No licence grant; not redistributed. Fetched for local analysis only."),
    ("Kurdistan", "12.", None, ".xlsx", "Sheet1",
     "CC BY 4.0",
     "https://data.mendeley.com/datasets/2cggk44f6g/2",
     "manual", "",
     "Secondary etiology track (8 classes, PCOS n=46). Mendeley: download manually."),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


rows = []
for name, prefix, must, ext, sheet, lic, url, method, slug, note in SOURCES:
    hit = None
    for p in sorted(TAB.iterdir()):
        if not p.name.startswith(prefix):
            continue
        if must and must not in p.name:
            continue
        if p.suffix.lower() != ext:
            continue
        hit = p
        break
    if hit is None:
        print(f"MISSING: {name}")
        continue
    rows.append(dict(
        collection=name, filename=hit.name, sheet=sheet or "",
        bytes=hit.stat().st_size, sha256=sha256(hit),
        licence=lic, url=url, method=method, locator=slug, notes=note,
        hashed_on=date.today().isoformat(), retrieval_date="",
    ))

df = pd.DataFrame(rows)
df.to_csv(MAN / "sources.csv", index=False)
print(df[["collection", "method", "bytes", "sha256"]].to_string(index=False))
