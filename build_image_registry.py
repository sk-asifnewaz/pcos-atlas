#!/usr/bin/env python
"""
Image-side registry for PCOS-HARM.

The image modality does not contribute to the binary core, but the reason must be
auditable rather than asserted. This emits one row per image catalogue entry with
its licence, dedup state, task type and inclusion decision.
"""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
WORKS = HERE.parent
ATLAS = WORKS / "atlas"
IMAGES = HERE / "images"
IMAGES.mkdir(exist_ok=True)

# entry number -> atlas dataset name
NUM2NAME = {
    1: "Anagha_Choudhari", 2: "ibadeus", 3: "PCOSGen_train", 4: "PCOSGen_test",
    5: "Indirani_A", 6: "BORAN_TOKTAY", 7: "Shweta_2000", 8: "researchworks",
    9: "Busakorn", 10: "VanessaS", 11: "MMOTU", 12: "impro_yvqsf", 13: "Borna",
}

# parse the image catalogue for licence + link
cat = pd.read_csv(WORKS / "Image" / "Image Datasets.csv", header=None)
lic, link = {}, {}
for _, r in cat.iterrows():
    v = str(r[0]).strip()
    if v.isdigit() and int(v) in NUM2NAME:
        lic[NUM2NAME[int(v)]] = str(r[5]).strip()
        link[NUM2NAME[int(v)]] = str(r[6]).strip()

TASK = {
    "Anagha_Choudhari": "classification", "ibadeus": "classification",
    "PCOSGen_train": "classification", "PCOSGen_test": "classification",
    "Indirani_A": "classification", "BORAN_TOKTAY": "classification",
    "Shweta_2000": "classification", "Borna": "classification",
    "researchworks": "detection", "Busakorn": "detection",
    "VanessaS": "detection", "impro_yvqsf": "detection",
    "MMOTU": "segmentation",
}

DECISION = {
    "Anagha_Choudhari": ("excluded", "sourcing artefact (metadata AUROC 1.000); hub of the shared image pool"),
    "ibadeus": ("excluded", "sourcing artefact; Grad-CAM on ruler overlay; byte-identical to Indirani_A"),
    "Indirani_A": ("excluded", "byte-identical duplicate of ibadeus (0 MD5 mismatches)"),
    "Shweta_2000": ("excluded", "97.28% of its images are contained in Anagha_Choudhari"),
    "BORAN_TOKTAY": ("excluded", "100% contained in Anagha_Choudhari; inverted label semantics"),
    "PCOSGen_train": ("excluded", "88.88% of its images are found inside ibadeus"),
    "PCOSGen_test": ("excluded", "63.28% overlap with PCOSGen_train; 58.45% inside ibadeus"),
    "MMOTU": ("excluded", "ovarian tumour segmentation, not PCOS"),
    "researchworks": ("detection_only", "YOLO class ids are object classes, not PCOS diagnosis"),
    "Busakorn": ("detection_only", "YOLO class ids are object classes, not PCOS diagnosis"),
    "VanessaS": ("detection_only", "YOLO class ids are object classes, not PCOS diagnosis"),
    "impro_yvqsf": ("detection_only", "YOLO class ids are object classes, not PCOS diagnosis"),
    "Borna": ("retained", "cleanest collection: 0 cross-split leakage, 0 cross-dataset overlap, 3 classes"),
}

PERMISSIVE = {"CC0", "CC0 1.0", "CC0: Public Domain", "Public Domain", "MIT",
              "CC BY 4.0", "Creative Commons Attribution 4.0 International",
              "Attribution 4.0 International (CC BY 4.0)", "Apache-2.0 license",
              "CC BY 4.0 License."}


def tier(l: str) -> str:
    l = str(l).strip()
    if l in PERMISSIVE:
        return "permissive"
    if l in {"CC BY-NC-SA 4.0"}:
        return "noncommercial_sharealike"
    if l in {"CC BY-NC 4.0"}:
        return "noncommercial"
    return "unknown_do_not_redistribute"


atlas = pd.read_csv(ATLAS / "TableS1_verification_atlas.csv",
                    encoding="utf-8", encoding_errors="replace")
atlas.columns = [c.strip() for c in atlas.columns]
base = (atlas[atlas["modality"] == "image"]
        [["dataset", "n_rows", "metadata_only_auroc", "pct_cross_dataset_overlap"]]
        .rename(columns={"n_rows": "n_images"}))
img = pd.read_csv(ATLAS / "atlas_image.csv")
img = base.merge(img.drop(columns=["n_images"]), on="dataset", how="left")
rows = []
for _, r in img.iterrows():
    name = r["dataset"]
    dec, why = DECISION.get(name, ("unclassified", ""))
    rows.append(dict(
        dataset=name,
        task=TASK.get(name, ""),
        licence=lic.get(name, ""),
        licence_tier=tier(lic.get(name, "")),
        source_url=link.get(name, ""),
        n_images=r["n_images"],
        n_unique_after_dedup=r.get("n_unique_after_dedup"),
        n_within_dup_excess=r.get("n_within_dup_excess"),
        pct_within_dup=r.get("pct_within_dup"),
        n_cross_split_pairs=r.get("n_cross_split_pairs"),
        pct_cross_split_overlap=r.get("pct_cross_split_overlap"),
        pct_cross_dataset_overlap=r["pct_cross_dataset_overlap"],
        metadata_only_auroc=r["metadata_only_auroc"],
        decision=dec,
        reason=why,
    ))

reg = pd.DataFrame(rows).sort_values(["decision", "dataset"])
reg.to_csv(IMAGES / "image_registry.csv", index=False)

retained = reg[reg["decision"] == "retained"]
det = reg[reg["decision"] == "detection_only"]
exc = reg[reg["decision"] == "excluded"]

lines = [
    "# Image track",
    "",
    "The image modality is **not** part of the binary core. This folder records why,",
    "so the exclusion is auditable rather than asserted.",
    "",
    f"- catalogue entries: **{len(reg)}**",
    f"- retained as a clean classification set: **{len(retained)}** "
    f"({int(retained['n_unique_after_dedup'].sum())} unique images)",
    f"- detection-only (no diagnosis label): **{len(det)}**",
    f"- excluded (duplicate, artefact, or not PCOS): **{len(exc)}**",
    "",
    "## Why the image side yields almost nothing",
    "",
    "1. **One pool, many names.** Anagha_Choudhari, Shweta_2000 and BORAN_TOKTAY are one",
    "   image pool presented three ways (97.3-100% containment). ibadeus and Indirani_A are",
    "   byte-identical across all 11,784 files. PCOSGen_train is 88.9% contained in ibadeus.",
    "2. **Detection is not diagnosis.** researchworks, Busakorn, VanessaS and impro_yvqsf",
    "   carry YOLO boxes whose class ids are object classes (follicle, ovary), not PCOS",
    "   status. They cannot be converted into a classification label without inventing one.",
    "3. **What is left is small.** After excluding the pool, the duplicates and the",
    "   detection sets, the only clean independent classification collection is **Borna**:",
    "   " + (f"{int(retained['n_unique_after_dedup'].sum())} unique images, 3 classes "
         "(Normal / Dominant_Follicle / PCO), 0 cross-split leakage, 0 cross-dataset overlap."
         if len(retained) else "none."),
    "",
    "That is a validation set, not a corpus. Adding it to PCOS-HARM would not strengthen",
    "the dataset; it would invite the objection that the image half is decorative.",
    "",
    "## Retained",
    "",
]
for _, r in retained.iterrows():
    lines.append(f"- **{r['dataset']}** - {int(r['n_unique_after_dedup'])} unique images, "
                 f"{r['task']}, {r['licence']}")
lines += ["", "## Excluded", "", "| dataset | images | unique after dedup | licence | reason |",
          "|---|---:|---:|---|---|"]
for _, r in exc.iterrows():
    lines.append(f"| {r['dataset']} | {int(r['n_images'])} | "
                 f"{'' if pd.isna(r['n_unique_after_dedup']) else int(r['n_unique_after_dedup'])} | "
                 f"{r['licence']} | {r['reason']} |")
lines += ["", "## Detection-only", "", "| dataset | images | unique after dedup | licence |",
          "|---|---:|---:|---|"]
for _, r in det.iterrows():
    lines.append(f"| {r['dataset']} | {int(r['n_images'])} | "
                 f"{int(r['n_unique_after_dedup'])} | {r['licence']} |")

(IMAGES / "README.md").write_text("\n".join(lines), encoding="utf-8")

print(f"image entries={len(reg)} retained={len(retained)} "
      f"retained_unique={int(retained['n_unique_after_dedup'].sum())} "
      f"detection={len(det)} excluded={len(exc)}")
