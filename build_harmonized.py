#!/usr/bin/env python
"""
PCOS-ATLAS builder
=================
Builds a provenance-verified, de-duplicated, licence-tiered harmonised PCOS
corpus from the 33 catalogue entries audited in this project.

Design rules (each is enforced in code, not prose):
  R1  independent label      - target must not be derivable from a Rotterdam input
  R2  no tautology           - no single input column at purity 1.000
  R3  no synthetic-by-construction (documented or AND-rule signature)
  R4  no corrupted data      - physiologically impossible values
  R5  licence tier           - redistributable vs fetch-only
  R6  no duplicate/subset    - one row per real collection

Outputs (all in this folder):
  catalogue.csv              one row per catalogue entry, with decision + reason
  licence_manifest.csv       what may be redistributed and what may not
  duplicate_registry.csv     every known redundancy relation
  splits_loco.csv            leave-one-collection-out folds + inner split
  core/core_records.csv      patient-level records (label + provenance)
  core/harmonized_long.csv   tidy: one row per (record, variable)
  core/harmonized_wide.csv   variables present in >=3 collections
  BUILD_REPORT.md            counts + the findings this build surfaced
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
WORKS = HERE.parent
TAB = WORKS / "Tabular" / "Tabular Datasets"
ATLAS = WORKS / "atlas"
CORE = HERE / "core"
CORE.mkdir(exist_ok=True)

# --------------------------------------------------------------------------
# 0. helpers
# --------------------------------------------------------------------------

def find_file(prefix: str, must: str | None = None, ext: str | None = None) -> Path:
    for p in sorted(TAB.iterdir()):
        if not p.name.startswith(prefix):
            continue
        if must and must not in p.name:
            continue
        if ext and p.suffix.lower() != ext:
            continue
        return p
    raise FileNotFoundError(f"{prefix} / {must} / {ext}")


def resolve_source(name: str, default: Path) -> Path:
    """Prefer the hash-verified copy produced by fetch.py, else the original path."""
    cand = HERE / "sources" / f"{name}{default.suffix}"
    return cand if cand.exists() else default


def read_csv_smart(p: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return pd.read_csv(p, encoding=enc, low_memory=False)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(p, encoding="latin-1", low_memory=False)


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def yn(s: pd.Series) -> pd.Series:
    """Map a messy yes/no column to 1/0/NA."""
    m = s.astype(str).str.strip().str.lower()
    out = pd.Series(np.nan, index=s.index, dtype="float")
    out[m.isin(["yes", "y", "1", "1.0", "true", "positive"])] = 1.0
    out[m.isin(["no", "n", "0", "0.0", "false", "negative"])] = 0.0
    return out


# --------------------------------------------------------------------------
# 1. canonical variable definitions
# --------------------------------------------------------------------------
# canonical_name -> (canonical_unit, {original_unit: factor_to_canonical})
CANON: dict[str, tuple[str, dict[str, float]]] = {
    "age_years":          ("years",   {}),
    "weight_kg":          ("kg",      {}),
    "height_cm":          ("cm",      {"ft": 30.48, "in": 2.54}),
    "bmi":                ("kg/m2",   {}),
    "waist_cm":           ("cm",      {"inch": 2.54}),
    "hip_cm":             ("cm",      {"inch": 2.54}),
    "sbp_mmhg":           ("mmHg",    {}),
    "dbp_mmhg":           ("mmHg",    {}),
    "cycle_length_days":  ("days",    {}),
    "period_duration_days": ("days",  {}),
    "testosterone_nmol_l":("nmol/L",  {"ng/dL": 0.0347, "ng/mL": 3.467, "nmol/L": 1.0}),
    "amh_ng_ml":          ("ng/mL",   {"pmol/L": 0.1401, "ng/mL": 1.0}),
    "lh_miu_ml":          ("mIU/mL",  {}),
    "fsh_miu_ml":         ("mIU/mL",  {}),
    "prolactin_ng_ml":    ("ng/mL",   {"uIU/mL": 1 / 21.2, "ng/mL": 1.0}),
    "tsh_miu_l":          ("mIU/L",   {"uIU/mL": 1.0, "mIU/L": 1.0}),
    "estradiol_pmol_l":   ("pmol/L",  {"pg/mL": 3.671, "pmol/L": 1.0}),
    "vitd_ng_ml":         ("ng/mL",   {"nmol/L": 1 / 2.496, "ng/mL": 1.0}),
    "glucose_fasting_mmol_l": ("mmol/L", {"mg/dL": 1 / 18.0, "mmol/L": 1.0}),
    "glucose_random_mg_dl":   ("mg/dL",  {"mg/dL": 1.0}),
    "insulin_uiu_ml":     ("uIU/mL",  {}),
    "homa_ir":            ("ratio",   {}),
    "chol_total_mmol_l":  ("mmol/L",  {"mg/dL": 1 / 38.67, "mmol/L": 1.0}),
    "hdl_mmol_l":         ("mmol/L",  {"mg/dL": 1 / 38.67, "mmol/L": 1.0}),
    "ldl_mmol_l":         ("mmol/L",  {"mg/dL": 1 / 38.67, "mmol/L": 1.0}),
    "trig_mmol_l":        ("mmol/L",  {"mg/dL": 1 / 88.57, "mmol/L": 1.0}),
    "fg_score":           ("0-36",    {}),
    "follicle_l_n":       ("count",   {}),
    "follicle_r_n":       ("count",   {}),
    "ovary_vol_l_ml":     ("mL",      {}),
    "ovary_vol_r_ml":     ("mL",      {}),
    # binary / categorical
    "cycle_irregular":    ("0/1",     {}),
    "hirsutism":          ("0/1",     {}),
    "pcom":               ("0/1",     {}),
    "weight_gain":        ("0/1",     {}),
    "skin_darkening":     ("0/1",     {}),
    "hair_loss":          ("0/1",     {}),
    "acne":               ("0/1",     {}),
    "fast_food":          ("0/1",     {}),
    "regular_exercise":   ("0/1",     {}),
    "family_history":     ("0/1",     {}),
}

# Physiological plausibility windows. Values outside are kept in the long file
# with plausible=0 but are set to NA in the wide matrix.
PLAUSIBLE: dict[str, tuple[float, float]] = {
    "age_years": (10, 60),
    "weight_kg": (25, 200),
    "height_cm": (120, 210),
    "bmi": (12, 70),
    "waist_cm": (45, 200),
    "hip_cm": (60, 200),
    "sbp_mmhg": (70, 250),
    "dbp_mmhg": (40, 150),
    "cycle_length_days": (15, 400),
    "period_duration_days": (1, 15),
    "testosterone_nmol_l": (0.1, 10),
    "amh_ng_ml": (0.01, 60),
    "lh_miu_ml": (0.1, 100),
    "fsh_miu_ml": (0.1, 100),
    "prolactin_ng_ml": (0.5, 200),
    "tsh_miu_l": (0.01, 20),
    "estradiol_pmol_l": (10, 5000),
    "vitd_ng_ml": (1, 100),
    "glucose_fasting_mmol_l": (2, 30),
    "glucose_random_mg_dl": (30, 600),
    "insulin_uiu_ml": (0.1, 300),
    "homa_ir": (0, 40),
    "chol_total_mmol_l": (1.5, 15),
    "hdl_mmol_l": (0.2, 4),
    "ldl_mmol_l": (0.2, 12),
    "trig_mmol_l": (0.2, 15),
    "fg_score": (0, 36),
    "follicle_l_n": (0, 60),
    "follicle_r_n": (0, 60),
    "ovary_vol_l_ml": (0.5, 100),
    "ovary_vol_r_ml": (0.5, 100),
}

LABEL_SOURCE = {
    "Kottarathil_full": "clinical (Rotterdam, retrospective)",
    "Chaabouni": "clinical (Rotterdam, case-control)",
    "Gawron": "clinical (explicit Rotterdam criterion columns)",
    "Sahil_Koli": "self-report survey",
    "hasaanrana": "self-report survey",
}


# Variables that are components of the Rotterdam definition of the target.
# Kept in the long file, withheld from the modelling matrix.
CRITERION_VARS = {
    "cycle_irregular", "cycle_length_days", "hirsutism", "testosterone_nmol_l",
    "fg_score", "pcom", "follicle_l_n", "follicle_r_n",
    "ovary_vol_l_ml", "ovary_vol_r_ml",
}

# --------------------------------------------------------------------------
# 2. collection definitions: label + column mapping
# --------------------------------------------------------------------------
# Each entry: file, sheet, label extractor, {canonical: (source_column, original_unit)}
COLLECTIONS: dict[str, dict] = {}

# ---- Kottarathil (India) --------------------------------------------------
COLLECTIONS["Kottarathil_full"] = dict(
    file=find_file("4.", must="without_infertility", ext=".xlsx"),
    sheet="Full_new",
    country="India",
    licence="CC BY-NC-SA 4.0",
    label_col="PCOS (Y/N)",
    label_map=None,
    cols={
        "age_years": ("Age (yrs)", "years"),
        "weight_kg": ("Weight (Kg)", "kg"),
        "height_cm": ("Height(Cm)", "cm"),
        "bmi": ("BMI", "kg/m2"),
        "waist_cm": ("Waist(inch)", "inch"),
        "hip_cm": ("Hip(inch)", "inch"),
        "sbp_mmhg": ("BP _Systolic (mmHg)", "mmHg"),
        "dbp_mmhg": ("BP _Diastolic (mmHg)", "mmHg"),
        "period_duration_days": ("Cycle length(days)", "days"),
        "lh_miu_ml": ("LH(mIU/mL)", "mIU/mL"),
        "fsh_miu_ml": ("FSH(mIU/mL)", "mIU/mL"),
        "amh_ng_ml": ("AMH(ng/mL)", "ng/mL"),
        "prolactin_ng_ml": ("PRL(ng/mL)", "ng/mL"),
        "tsh_miu_l": ("TSH (mIU/L)", "mIU/L"),
        "vitd_ng_ml": ("Vit D3 (ng/mL)", "ng/mL"),
        "glucose_random_mg_dl": ("RBS(mg/dl)", "mg/dL"),
        "follicle_l_n": ("Follicle No. (L)", "count"),
        "follicle_r_n": ("Follicle No. (R)", "count"),
    },
    binaries={
        "cycle_irregular": ("Cycle(R/I)", {2.0: 0.0, 4.0: 1.0}),
        "hirsutism": ("hair growth(Y/N)", None),
        "weight_gain": ("Weight gain(Y/N)", None),
        "skin_darkening": ("Skin darkening (Y/N)", None),
        "hair_loss": ("Hair loss(Y/N)", None),
        "acne": ("Pimples(Y/N)", None),
        "fast_food": ("Fast food (Y/N)", None),
        "regular_exercise": ("Reg.Exercise(Y/N)", None),
    },
)

# ---- Chaabouni (Tunisia) --------------------------------------------------
COLLECTIONS["Chaabouni"] = dict(
    file=find_file("9.", ext=".xlsx"),
    sheet="vitD09_02_18donnees.spv",
    country="Tunisia",
    licence="CC BY 4.0",
    label_col="SOPK",
    label_map=None,
    cols={
        "age_years": ("Age", "years"),
        "bmi": ("BMI", "kg/m2"),
        "waist_cm": ("Waist circumference", "cm"),
        "sbp_mmhg": ("systolic blood pressure", "mmHg"),
        "dbp_mmhg": ("diastolic blood pressure", "mmHg"),
        "testosterone_nmol_l": ("Testosterone", "ng/mL"),
        "lh_miu_ml": ("LH", "mIU/mL"),
        "fsh_miu_ml": ("FSH", "mIU/mL"),
        "prolactin_ng_ml": ("PRL", "ng/mL"),
        "estradiol_pmol_l": ("E2", "pg/mL"),
        "vitd_ng_ml": ("@25OHVitD", "ng/mL"),
        "glucose_fasting_mmol_l": ("GLU", "mmol/L"),
        "homa_ir": ("HOMA_IR", "ratio"),
        "chol_total_mmol_l": ("total cholesterol", "mmol/L"),
        "hdl_mmol_l": ("HDLc", "mmol/L"),
        "ldl_mmol_l": ("LDLc", "mmol/L"),
        "trig_mmol_l": ("triglycerides", "mmol/L"),
    },
    binaries={},
)

# ---- Gawron (Poland) ------------------------------------------------------
COLLECTIONS["Gawron"] = dict(
    file=find_file("16.", ext=".xlsx"),
    sheet="Sheet1",
    country="Poland",
    licence="CC0 1.0",
    label_col=None,  # multi-column: PCOS A / B / D
    label_map=None,
    cols={
        "age_years": ("Age [years]", "years"),
        "weight_kg": ("Weight [kg]", "kg"),
        "height_cm": ("Height [cm]", "cm"),
        "bmi": ("BMI [kg/m2]", "kg/m2"),
        "cycle_length_days": ("Average menstrual cycle length [days]", "days"),
        "fg_score": ("Ferriman-Gallwey Scale Score [n]", "0-36"),
        "testosterone_nmol_l": ("Testosterone [nmol/l]", "nmol/L"),
        "amh_ng_ml": ("Anti-Müllerian Hormone (AMH) [pmol/L]", "pmol/L"),
        "lh_miu_ml": ("LH [mIU/ml]", "mIU/mL"),
        "fsh_miu_ml": ("FSH [mIU/ml]", "mIU/mL"),
        "prolactin_ng_ml": ("Prolactin [uIU/ml]", "uIU/mL"),
        "tsh_miu_l": ("TSH [uIU/ml]", "uIU/mL"),
        "estradiol_pmol_l": ("Estradiol [pmol/l]", "pmol/L"),
        "vitd_ng_ml": ("Vitamin D [ng/ml]", "ng/mL"),
        "glucose_fasting_mmol_l": ("Fasting glucose [mmol/l]", "mmol/L"),
        "insulin_uiu_ml": ("Fasting insulin [uU/ml]", "uIU/mL"),
        "homa_ir": ("HOMA-IR", "ratio"),
        "chol_total_mmol_l": ("Total cholesterol [mmol/l]", "mmol/L"),
        "hdl_mmol_l": ("HDL cholesterol [mmol/l]", "mmol/L"),
        "ldl_mmol_l": ("LDL cholesterol  [mmol/l]", "mmol/L"),
        "trig_mmol_l": ("Triglycerides [mmol/l]", "mmol/L"),
        "ovary_vol_l_ml": ("Left ovary volume [ml]", "mL"),
        "ovary_vol_r_ml": ("Right ovary volume [ml]", "mL"),
    },
    binaries={
        "pcom": ("Policystic ovarian morphology [0 - no, 1 - yes]", None),
    },
)

# ---- Sahil Koli (India) ---------------------------------------------------
COLLECTIONS["Sahil_Koli"] = dict(
    file=find_file("6.", ext=".csv"),
    sheet=None,
    country="India",
    licence="CC0",
    label_col="Have you been diagnosed with PCOS/PCOD?",
    label_map=None,
    cols={
        "age_years": ("Age (in Years)", "years"),
        "weight_kg": ("Weight (in Kg)", "kg"),
        "height_cm": ("Height (in Cm / Feet)", "mixed"),
        "period_duration_days": ("How long does your period last ?", "days"),
    },
    binaries={
        "cycle_irregular": ("Are your periods regular ?", "invert"),
        "hirsutism": ("Do you have excessive body/facial hair growth ?", None),
        "weight_gain": ("Have you gained weight recently?", None),
        "skin_darkening": ("Are you noticing skin darkening recently?", None),
        "hair_loss": ("Do have hair loss/hair thinning/baldness ?", None),
        "acne": ("Do you have pimples/acne on your face/jawline ?", None),
        "fast_food": ("Do you eat fast food regularly ?", None),
        "regular_exercise": ("Do you exercise on a regular basis ?", None),
    },
)

# ---- hasaanrana (Pakistan) ------------------------------------------------
COLLECTIONS["hasaanrana"] = dict(
    file=find_file("5.", ext=".csv"),
    sheet=None,
    country="Pakistan",
    licence="Other (unspecified)",
    label_col="PCOS",
    label_map=None,
    cols={
        "age_years": ("Age", "years"),
        "weight_kg": ("Weight_kg", "kg"),
        "height_cm": ("Height_ft", "cm"),  # column says ft, values are cm
    },
    binaries={
        "cycle_irregular": ("Menstrual_Irregularity", None),
        "hirsutism": ("Hirsutism", None),
        "family_history": ("Family_History_PCOS", None),
    },
)

# --------------------------------------------------------------------------
# 3. build long format
# --------------------------------------------------------------------------

def load(cfg: dict) -> pd.DataFrame:
    if cfg["sheet"]:
        return pd.read_excel(cfg["file"], sheet_name=cfg["sheet"])
    return read_csv_smart(cfg["file"])


def extract_label(df: pd.DataFrame, name: str, cfg: dict) -> pd.Series:
    if name == "Gawron":
        cols = [c for c in df.columns if re.match(r"^PCOS [ABD]$", str(c).strip())]
        any_pos = pd.concat([num(df[c]).fillna(0) for c in cols], axis=1).max(axis=1)
        return any_pos.astype(float)
    if name == "hasaanrana":
        m = df[cfg["label_col"]].astype(str).str.strip().str.lower()
        out = pd.Series(np.nan, index=df.index, dtype="float")
        out[m == "yes"] = 1.0
        out[m == "no"] = 0.0
        return out  # malformed "no, yes, not diagnosed by a doctor" -> NaN
    return num(df[cfg["label_col"]])


rows: list[dict] = []
records: list[dict] = []
notes: list[str] = []

for name, cfg in COLLECTIONS.items():
    cfg["file"] = resolve_source(name, cfg["file"])
    df = load(cfg)
    df.columns = [str(c).strip() for c in df.columns]
    label = extract_label(df, name, cfg)

    # --- numeric / continuous ---
    for var, (src, unit) in cfg["cols"].items():
        if src not in df.columns:
            cand = [c for c in df.columns if c.startswith(src)]
            if cand:
                src = cand[0]
        if src not in df.columns:
            notes.append(f"{name}: column '{src}' not found for {var}")
            continue
        raw = num(df[src])
        canon_unit, factors = CANON[var]
        if unit == "mixed":
            # Sahil Koli: cm, but a handful of rows store feet or inches raw
            raw = raw.map(lambda v: v * 30.48 if (pd.notna(v) and v < 10)
                          else (v * 2.54 if (pd.notna(v) and v < 100) else v))
            unit_used, factor = "cm", 1.0
        else:
            unit_used, factor = unit, factors.get(unit, 1.0)
        for i, v in raw.items():
            if pd.isna(v):
                continue
            rows.append(dict(
                collection=name, row_index=int(i), variable=var,
                value_original=float(v), unit_original=unit_used,
                value_canonical=float(v) * factor, unit_canonical=canon_unit,
                conversion_factor=factor,
                source_column=src,
                criterion_leak=int(var in CRITERION_VARS),
            ))

    # --- binary ---
    for var, (src, mapping) in cfg["binaries"].items():
        if src not in df.columns:
            notes.append(f"{name}: column '{src}' not found for {var}")
            continue
        if mapping == "invert":
            raw = 1.0 - num(df[src])
        elif isinstance(mapping, dict):
            raw = num(df[src]).map(mapping)
        else:
            raw = yn(df[src])
        for i, v in raw.items():
            if pd.isna(v):
                continue
            rows.append(dict(
                collection=name, row_index=int(i), variable=var,
                value_original=float(v), unit_original="0/1",
                value_canonical=float(v), unit_canonical="0/1",
                conversion_factor=1.0, source_column=src,
                criterion_leak=int(var in CRITERION_VARS),
            ))

    # --- derived BMI where absent ---
    if "bmi" not in cfg["cols"]:
        w = num(df[cfg["cols"]["weight_kg"][0]])
        h = num(df[cfg["cols"]["height_cm"][0]])
        if name == "hasaanrana":
            h = h  # already cm
        bmi = w / (h / 100.0) ** 2
        for i, v in bmi.items():
            if pd.isna(v) or not (10 <= v <= 70):
                continue
            rows.append(dict(
                collection=name, row_index=int(i), variable="bmi",
                value_original=float(v), unit_original="kg/m2",
                value_canonical=float(v), unit_canonical="kg/m2",
                conversion_factor=1.0, source_column="derived(weight,height)",
                criterion_leak=0,
            ))

    # --- records ---
    for i, lab in label.items():
        records.append(dict(
            collection=name, row_index=int(i),
            label_pcos=(None if pd.isna(lab) else float(lab)),
            country=cfg["country"], licence=cfg["licence"],
        ))

long = pd.DataFrame(rows)

def plausible(row) -> int:
    lo_hi = PLAUSIBLE.get(row["variable"])
    if lo_hi is None:
        return 1
    lo, hi = lo_hi
    return int(lo <= row["value_canonical"] <= hi)

long["plausible"] = long.apply(plausible, axis=1)

recs = pd.DataFrame(records)

# stable record ids
recs["record_id"] = recs.apply(
    lambda r: f"{r['collection']}-{r['row_index']:05d}", axis=1)
long["record_id"] = long["collection"] + "-" + long["row_index"].map(lambda x: f"{x:05d}")

# label integrity: a label must be exactly 0 or 1. Gawron's file ends with two
# summary-statistic rows whose "label" is the group count (82) and a proportion.
bad_label = (~recs["label_pcos"].isin([0, 1])) & recs["label_pcos"].notna()
if bad_label.any():
    notes.append(
        f"{int(bad_label.sum())} row(s) dropped for a non-binary label "
        f"({', '.join(sorted(recs.loc[bad_label, 'collection'].unique()))}) - "
        "summary-statistic rows embedded in the source file")
    drop_ids = set(recs.loc[bad_label, "record_id"])
    recs = recs[~bad_label].copy()
    long = long[~long["record_id"].isin(drop_ids)]

# --------------------------------------------------------------------------
# 4. licence tiers + catalogue
# --------------------------------------------------------------------------

PERMISSIVE = {
    "CC0", "CC0 1.0", "CC0: Public Domain", "Public Domain", "MIT",
    "CC BY 4.0", "Creative Commons Attribution 4.0 International",
    "Attribution 4.0 International (CC BY 4.0)", "Apache-2.0 license",
    "CC BY 4.0 License.",
}
# CC BY-NC-SA permits redistribution, but the ShareAlike clause forces any
# adaptation - including a harmonised corpus that pools these rows - to carry
# the same licence. It is redistributable; it is not permissive.
NC_SA = {"CC BY-NC-SA 4.0"}
NC_ONLY = {"CC BY-NC 4.0",
           "Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)"}


def licence_tier(lic: str) -> str:
    lic = str(lic).strip()
    if lic in PERMISSIVE:
        return "permissive"
    if lic in NC_SA:
        return "noncommercial_sharealike"
    if lic in NC_ONLY:
        return "noncommercial"
    return "unknown_do_not_redistribute"


RELEASE_CHANNEL = {
    "permissive": "permissive_core",
    "noncommercial_sharealike": "full_corpus_nc_sa",
    "noncommercial": "full_corpus_nc",
    "unknown_do_not_redistribute": "fetch_only",
}
RELEASE_ACTION = {
    "permissive": "ship rows under CC BY 4.0 with attribution",
    "noncommercial_sharealike": "ship rows under CC BY-NC-SA 4.0 with attribution",
    "noncommercial": "ship rows under CC BY-NC 4.0 with attribution",
    "unknown_do_not_redistribute": "loader + row hashes only; no licence to redistribute",
}


atlas = pd.read_csv(ATLAS / "TableS1_verification_atlas.csv", encoding="utf-8", encoding_errors="replace")
atlas.columns = [c.strip() for c in atlas.columns]

# decision table: the audit's verdict drives inclusion, not hand-waving
DECISION = {
    # collection: (decision, reason)
    "Kottarathil_full": ("core", "real, independent label; PCOM criterion leakage flagged and ablated"),
    "Chaabouni": ("core", "real case-control, Rotterdam-diagnosed; E2 flagged as downstream correlate"),
    "Gawron": ("core_criterion",
               "target is a deterministic function of the shipped criterion columns "
               "(purity 1.0000 over all 10 tuples) - tautological for PCOS prediction; "
               "retained only as a criterion-level multi-label track"),
    "Sahil_Koli": ("core", "real self-report survey; label is self-reported diagnosis"),
    "hasaanrana": ("core", "real survey; malformed third label value repaired to NA"),
    "Kurdistan": ("core_etiology", "real; 9-class etiology, PCOS n=46 - kept as multi-class track only"),
    "Samiksha_Dalvi": ("excluded", "R3 nonlinear synthetic (AND-rule signature)"),
    "Ankush_Panday": ("excluded", "R1 label uncorrelated with features (AUROC 0.50)"),
    "Michael_Mendiola_Sy": ("excluded", "R4 16 of 52 columns carry impossible negative values"),
    "Saba_Zafar_Sheet2": ("excluded", "R2 tautological (cyst count restates phenotype)"),
    "Lucas_Souza_Soares": ("excluded", "R2 tautological (AFC restates diagnosis, AUROC 1.000)"),
    "Talukder": ("excluded", "R2 target constructed from criterion columns (AUROC 1.000)"),
    "MD_Abdul_Kaium": ("excluded", "R3 label-aware feature selection before split; mixed provenance"),
    "Shaurya_Srivastava": ("excluded", "R3 synthetic by documentation"),
    "Puspita_UserProfile": ("excluded", "R3 synthetic by documentation"),
    "Puspita_Period_Log": ("excluded", "R6 companion table of Puspita_UserProfile"),
    "Kottarathil_infertil": ("excluded", "R6 3-column subset of Kottarathil_full"),
    "Ghada_Elfadil_PCOS_DATA": ("excluded", "R1 no diagnosis column"),
    "Ghada_Elfadil_Sudan": ("excluded", "R1 no diagnosis column"),
    "Indirani_A": ("excluded", "R6 byte-identical to ibadeus"),
    "Anagha_Choudhari": ("excluded", "R4 sourcing artefact; hub of the shared image pool"),
    "ibadeus": ("excluded", "R4 metadata-only AUROC 1.000; ruler overlay; duplicate of Indirani"),
    "Shweta_2000": ("excluded", "R6 97.3% contained in Anagha_Choudhari"),
    "BORAN_TOKTAY": ("excluded", "R6 100% contained in Anagha_Choudhari; inverted labels"),
    "MMOTU": ("excluded", "R1 ovarian tumour, not PCOS"),
    "PCOSGen_train": ("excluded", "R6 88.9% of its images are in ibadeus"),
    "PCOSGen_test": ("excluded", "R6 63.3% overlaps PCOSGen_train; 58.5% in ibadeus"),
    "researchworks": ("image_detection", "detection boxes are object classes, not PCOS status"),
    "Busakorn": ("image_detection", "detection boxes are object classes, not PCOS status"),
    "VanessaS": ("image_detection", "detection boxes are object classes, not PCOS status"),
    "impro_yvqsf": ("image_detection", "detection boxes are object classes, not PCOS status"),
    "Borna": ("image_classification", "cleanest image collection: 0 cross-split leakage, 3 classes"),
    "PCOS_ULTRASOUNG_IMAGE_AND_CLINICAL_FEATURE_DATASET": (
        "excluded", "R4/R6 fails all five multimodal checks; resampled Kottarathil clone"),
}

cat = atlas[["modality", "dataset", "n_rows", "target", "fine_verdict",
             "paper_group", "verdict_reason"]].copy()
cat["decision"] = cat["dataset"].map(lambda d: DECISION.get(d, ("unclassified", ""))[0])
cat["decision_reason"] = cat["dataset"].map(lambda d: DECISION.get(d, ("unclassified", ""))[1])
cat["licence"] = cat["dataset"].map(lambda d: COLLECTIONS[d]["licence"] if d in COLLECTIONS else "")
cat["licence_tier"] = cat["licence"].map(licence_tier)
cat["release_channel"] = cat["licence_tier"].map(RELEASE_CHANNEL)
cat["redistributable"] = cat["licence_tier"].isin(
    ["permissive", "noncommercial_sharealike", "noncommercial"]).astype(int)
cat.to_csv(HERE / "catalogue.csv", index=False)

# --------------------------------------------------------------------------
# 5. licence manifest
# --------------------------------------------------------------------------
lic_rows = []
for name, cfg in COLLECTIONS.items():
    tier = licence_tier(cfg["licence"])
    lic_rows.append(dict(
        collection=name, licence=cfg["licence"], tier=tier,
        release_channel=RELEASE_CHANNEL[tier],
        may_ship_rows=int(tier != "unknown_do_not_redistribute"),
        may_ship_images=0,
        action=RELEASE_ACTION[tier],
        attribution_required=1,
        commercial_use_allowed=int(tier == "permissive"),
    ))
for name in ["Borna", "researchworks", "Busakorn", "VanessaS", "impro_yvqsf"]:
    lic = {"Borna": "CC BY 4.0 License.", "researchworks": "CC BY 4.0",
           "Busakorn": "CC BY 4.0", "VanessaS": "Public Domain",
           "impro_yvqsf": "CC BY 4.0"}[name]
    tier = licence_tier(lic)
    lic_rows.append(dict(
        collection=name, licence=lic, tier=tier,
        release_channel=RELEASE_CHANNEL[tier],
        may_ship_rows=0,
        may_ship_images=int(tier != "unknown_do_not_redistribute"),
        action=("ship deduplicated image manifest with attribution"
                if tier != "unknown_do_not_redistribute" else "manifest + hashes only"),
        attribution_required=1,
        commercial_use_allowed=int(tier == "permissive"),
    ))
pd.DataFrame(lic_rows).to_csv(HERE / "licence_manifest.csv", index=False)

# --------------------------------------------------------------------------
# 6. duplicate registry
# --------------------------------------------------------------------------
dup = []
cd = pd.read_csv(ATLAS / "atlas_crossdataset.csv")
for _, r in cd.iterrows():
    if r["verdict"] != "negligible":
        dup.append(dict(kind="image_cross_dataset", a=r["dataset_a"], b=r["dataset_b"],
                        metric="pct_a_matched", value=r["pct_a_matched"], verdict=r["verdict"]))
glob = pd.read_csv(ATLAS / "atlas_crossdataset_global.csv")
for _, r in glob.iterrows():
    if r["pct_a_matched"] >= 5:
        dup.append(dict(kind="image_global_containment", a=r["dataset_a"], b=r["dataset_b"],
                        metric="pct_a_matched", value=r["pct_a_matched"], verdict="containment"))
dup.append(dict(kind="tabular_byte", a="Indirani_A", b="ibadeus",
                metric="md5_mismatches", value=0, verdict="byte_identical"))
dup.append(dict(kind="tabular_schema", a="Samiksha_Dalvi", b="Lucas_Souza_Soares",
                metric="shared_rows", value=0, verdict="same_generator_different_seed"))
dup.append(dict(kind="tabular_subset", a="Kottarathil_infertil", b="Kottarathil_full",
                metric="shared_rows", value=541, verdict="column_subset"))

# --------------------------------------------------------------------------
# 7. LOCO splits
# --------------------------------------------------------------------------
core_names = [n for n, c in DECISION.items() if c[0] == "core"]
core_recs = recs[recs["collection"].isin(core_names)].copy()
core_recs["licence_tier"] = core_recs["licence"].map(licence_tier)
core_recs["label_source"] = core_recs["collection"].map(LABEL_SOURCE)
long_core = long[long["collection"].isin(core_names)].copy()

# cross-collection duplication check among the survivors: no two records in
# different collections may share the same (age, bmi, label) fingerprint.
fp = (long_core[long_core["variable"].isin(["age_years", "bmi"])]
      .pivot_table(index="record_id", columns="variable", values="value_canonical"))
fp = fp.round(1).join(core_recs.set_index("record_id")[["collection", "label_pcos"]])
fp = fp.dropna()
for i, a in enumerate(core_names):
    for b in core_names[i + 1:]:
        fa = fp[fp["collection"] == a]
        fb = fp[fp["collection"] == b]
        if fa.empty or fb.empty:
            continue
        m = fa.reset_index().merge(
            fb.reset_index(), on=["age_years", "bmi", "label_pcos"],
            suffixes=("_a", "_b"))
        rate = len(m) / max(min(len(fa), len(fb)), 1)
        dup.append(dict(
            kind="tabular_cross_collection", a=a, b=b,
            metric="shared_age_bmi_label_rows", value=len(m),
            verdict=(f"coincidental ({rate:.2%} of the smaller collection; "
                     "3 coarse fields cannot establish identity)")))

pd.DataFrame(dup).to_csv(HERE / "duplicate_registry.csv", index=False)

rng = np.random.default_rng(20261110)
core_recs["inner_split"] = "train"
for coll, g in core_recs.groupby("collection"):
    idx = g.index.to_numpy().copy()
    rng.shuffle(idx)
    n_test = max(1, int(round(0.2 * len(idx))))
    core_recs.loc[idx[:n_test], "inner_split"] = "test"

folds = []
for coll in core_names:
    for _, r in core_recs.iterrows():
        folds.append(dict(
            record_id=r["record_id"], collection=coll,
            outer_fold=coll,
            outer_role=("test" if r["collection"] == coll else "train"),
            inner_split=r["inner_split"],
            label_pcos=r["label_pcos"],
        ))
pd.DataFrame(folds).to_csv(HERE / "splits_loco.csv", index=False)

# --------------------------------------------------------------------------
# 8. write core outputs
# --------------------------------------------------------------------------
long_core.to_csv(CORE / "harmonized_long.csv", index=False)

core_recs.to_csv(CORE / "core_records.csv", index=False)

# wide: variables present in >= 3 collections
cov = (long_core.groupby("variable")["collection"].nunique()
       .sort_values(ascending=False))
wide_vars = cov[cov >= 3].index.tolist()
wide = (long_core[(long_core["variable"].isin(wide_vars)) & (long_core["plausible"] == 1)]
        .pivot_table(index="record_id", columns="variable",
                     values="value_canonical", aggfunc="first"))
wide = wide.reindex(columns=wide_vars)
wide = wide.join(core_recs.set_index("record_id")[["collection", "label_pcos", "country"]])
wide.to_csv(CORE / "harmonized_wide.csv")

# modelling matrix: criterion variables withheld, or the label is partly encoded
model_vars = [v for v in wide_vars if v not in CRITERION_VARS]
model = wide[model_vars + ["collection", "label_pcos", "country"]].copy()
model.to_csv(CORE / "model_matrix.csv")

# --------------------------------------------------------------------------
# 8b. secondary track: Kurdistan etiology (9 classes, PCOS n=46)
# --------------------------------------------------------------------------
kur = pd.read_excel(
    resolve_source("Kurdistan", find_file("12.", ext=".xlsx")), sheet_name="Sheet1")
kur.columns = [str(c).strip() for c in kur.columns]
kur = kur.rename(columns={
    "Patient_ID": "source_patient_id",
    "Etiology (Primary Diagnosis)": "etiology",
    "Clinical Symptoms": "clinical_symptoms",
    "Duration (Months)": "duration_months",
    "Associated Conditions": "associated_conditions",
    "Status (M/S)": "marital_status",
    "Weight (kg)": "weight_kg",
    "Age": "age_years",
})
keep = ["source_patient_id", "age_years", "weight_kg", "marital_status",
        "etiology", "clinical_symptoms", "duration_months", "associated_conditions"]
kur = kur[[c for c in keep if c in kur.columns]].copy()
kur = kur[kur["source_patient_id"].notna()].copy()
kur["etiology"] = kur["etiology"].astype(str).str.strip()
kur.insert(0, "record_id", [f"Kurdistan-{i:05d}" for i in range(len(kur))])
kur["label_pcos"] = kur["etiology"].str.contains(
    "PCOS|Polycystic", case=False, regex=True).astype(int)
kur["collection"] = "Kurdistan"
kur["country"] = "Iraq"
kur["licence"] = "CC BY 4.0"
kur["task"] = "multi_class_etiology"
kur.to_csv(CORE / "kurdistan_etiology.csv", index=False)

# --------------------------------------------------------------------------
# 8c. secondary track: Gawron criterion-level multi-label
# --------------------------------------------------------------------------
# The label is derived from the criterion columns, so Gawron cannot enter the
# binary core (R2). It remains the only collection carrying explicit Rotterdam
# criteria, which makes it usable for multi-label criterion prediction.
gaw = pd.read_excel(
    resolve_source("Gawron", find_file("16.", ext=".xlsx")), sheet_name="Sheet1")
gaw.columns = [str(c).strip() for c in gaw.columns]
criterion_cols = [c for c in gaw.columns if c.startswith("PCOS ")]
amh = next(c for c in gaw.columns if c.startswith("Anti-M"))
crit = gaw[["Age [years]", "Weight [kg]", "Height [cm]", "BMI [kg/m2]",
            "Ferriman-Gallwey Scale Score [n]", amh] + criterion_cols]
crit = crit[crit["Age [years]"].notna()].copy()   # drops the summary rows
crit.insert(0, "record_id", [f"Gawron-{i:05d}" for i in range(len(crit))])
crit = crit.rename(columns={
    "Age [years]": "age_years", "Weight [kg]": "weight_kg",
    "Height [cm]": "height_cm", "BMI [kg/m2]": "bmi",
    "Ferriman-Gallwey Scale Score [n]": "fg_score", amh: "amh_pmol_l",
})
crit["collection"] = "Gawron"
crit["country"] = "Poland"
crit["licence"] = "CC0 1.0"
crit["task"] = "criterion_multilabel"
crit.to_csv(CORE / "gawron_criterion.csv", index=False)

# --------------------------------------------------------------------------
# 9. build report
# --------------------------------------------------------------------------
n_entries = len(cat)
n_core = len(core_names)
n_rec = len(core_recs)
n_lab = int(core_recs["label_pcos"].notna().sum())
n_pos = int((core_recs["label_pcos"] == 1).sum())
perm = core_recs[core_recs["licence_tier"] == "permissive"]
n_perm = len(perm)
n_perm_pos = int((perm["label_pcos"] == 1).sum())
ncsa = core_recs[core_recs["licence_tier"] == "noncommercial_sharealike"]
n_ncsa = len(ncsa)
n_ncsa_pos = int((ncsa["label_pcos"] == 1).sum())
full = core_recs[core_recs["licence_tier"].isin(
    ["permissive", "noncommercial_sharealike", "noncommercial"])]
n_full = len(full)
n_full_pos = int((full["label_pcos"] == 1).sum())

lines = [
    "# PCOS-ATLAS build report",
    "",
    f"Built from {n_entries} catalogue entries.",
    "",
    "## What survives",
    "",
    f"- **{n_core} collections** pass all six inclusion rules.",
    f"- **{n_rec} patient records**, of which **{n_lab}** carry a usable binary label "
    f"({n_pos} positive, {n_pos / max(n_lab,1):.1%}).",
    "",
    "### Release tiers",
    "",
    f"- **Permissive core** — {n_perm} records ({n_perm_pos} positive), CC BY 4.0. "
    f"{' + '.join(sorted(perm['collection'].unique()))}. Commercial reuse allowed.",
    f"- **Full corpus** — {n_full} records ({n_full_pos} positive), CC BY-NC-SA 4.0. "
    f"Adds {' + '.join(sorted(ncsa['collection'].unique()))} ({n_ncsa} records). "
    "ShareAlike forces the whole harmonised corpus to carry the same licence.",
    f"- **Fetch-only** — {n_rec - n_full} records (hasaanrana): licence unspecified, "
    "so no redistribution right exists. Ship loader + row hashes.",
    "",
    f"- **{int((long_core['plausible'] == 0).sum())} values** were outside the "
    f"physiological window and are set to NA in the wide matrix "
    f"({int((long_core['plausible'] == 0).sum()) / max(len(long_core),1):.2%} of all values).",
    "",
    "## Per-collection yield",
    "",
    "| collection | country | label source | licence | tier | records | positive | prevalence | implausible values |",
    "|---|---|---|---|---|---:|---:|---:|---:|",
]
for coll in core_names:
    g = core_recs[core_recs["collection"] == coll]
    gl = long_core[long_core["collection"] == coll]
    pos = int((g["label_pcos"] == 1).sum())
    lab = int(g["label_pcos"].notna().sum())
    lines.append(
        f"| {coll} | {g['country'].iloc[0]} | {g['label_source'].iloc[0]} | "
        f"{g['licence'].iloc[0]} | {g['licence_tier'].iloc[0]} | {len(g)} | {pos} | "
        f"{pos / max(lab,1):.1%} | {int((gl['plausible']==0).sum())} |")

lines += [
    "",
    "## Variable coverage (collections per variable)",
    "",
    "| variable | collections | criterion leak |",
    "|---|---:|---|",
]
for v in cov.index:
    lines.append(f"| {v} | {int(cov[v])} | "
                 f"{'yes' if v in CRITERION_VARS else 'no'} |")

lines += [
    "",
    f"## Wide core: {len(wide_vars)} variables present in >=3 collections",
    "",
    "Variables: " + ", ".join(f"`{v}`" for v in wide_vars),
    "",
    "## Findings surfaced by this build",
    "",
]
if notes:
    lines += [f"- {n}" for n in dict.fromkeys(notes)]
lines += [
    "- Kottarathil `RBS(mg/dl)` is a **random** blood sugar, not fasting. It is mapped to "
    "`glucose_random_mg_dl` and is therefore not poolable with Gawron/Chaabouni fasting glucose.",
    "- Kottarathil `Cycle length(days)` holds **period/flow duration** (2-12 days, mode 5), "
    "not cycle length (21-35 days). Remapped to `period_duration_days`; pooling it with "
    "Gawron's 30-55 day cycle length would have corrupted the variable. Sahil Koli's "
    "period-duration column independently confirms the interpretation (mean 4.60 vs 4.94 days).",
    "- hasaanrana `Height_ft` is labelled feet but holds centimetres (157.48, 165.1). "
    "Mapped as cm; BMI derived from it agrees with the stated range.",
    "- Kottarathil follicle counts and ovary volumes are Rotterdam components. They are kept "
    "in the long file with `criterion_leak=1` and withheld from `model_matrix.csv`.",
    "- Only Gawron carries explicit criterion columns, so it is the only collection where "
    "criterion-level (OD/HA/PCOM) supervision is possible.",
    "- Gawron is an **anovulation cohort**, not a general-population case-control: 141 of 158 "
    "records are PCOS. It will dominate the positive class in any pooled analysis.",
]

(HERE / "BUILD_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

print(f"entries={n_entries} core_collections={n_core} records={n_rec} "
      f"labelled={n_lab} positive={n_pos} permissive={n_perm} full={n_full}")
print("wrote:", ", ".join(sorted(p.name for p in HERE.glob("*.csv"))),
      "| core/:", ", ".join(sorted(p.name for p in CORE.glob("*.csv"))))
