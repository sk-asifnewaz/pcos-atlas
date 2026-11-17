# PCOS-ATLAS — a provenance-verified, de-duplicated harmonised PCOS corpus

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24326688.svg)](https://doi.org/10.5281/zenodo.24326688)

Built from the 33 catalogue entries audited in this project. **33 entries → 27 distinct
collections → 5 collections that survive verification → 1,425 patient records.**

This is not a "mega-dataset" assembled to raise an accuracy number. It is the subset of
public PCOS data that survives a provenance audit, expressed in one schema, with every
exclusion justified and every value traceable to its source column.

---

## 1. Why this exists

Li et al. (2025) audited 36 PCOS datasets, found 12 open, and named as their future work
*"developing a unified dataset to enable systematic comparison of detection tools."* This
is that dataset, built the only way it can honestly be built: by auditing first and
merging second.

The audit found that the apparent abundance of public PCOS data is largely an illusion.
Thirteen image collections collapse to one repackaged pool plus a handful of residuals.
Nineteen tabular entries collapse to seventeen collections, of which five are tautological
or synthetic, six are low-signal or corrupted, and two have no label at all.

What remains is small. That is the finding, not a defect.

---

## 2. Inclusion rules

A collection enters the core only if it passes **all six**. Each rule is enforced in
`build_harmonized.py`, not asserted in prose.

| # | Rule | Rejects |
|---|---|---|
| R1 | Independent label — the target must not be a function of a Rotterdam input | Talukder, MD_Abdul_Kaium |
| R2 | No tautology — no single input at purity 1.000 | Saba_Zafar, Lucas_Souza_Soares |
| R3 | Not synthetic by construction (documented or AND-rule signature) | Samiksha_Dalvi, Shaurya_Srivastava, Puspita |
| R4 | No corrupted data — physiologically impossible values | Michael_Mendiola_Sy |
| R5 | Licence permits redistribution (else fetch-only) | see §6 |
| R6 | Not a duplicate, subset or companion table | Kottarathil_infertil, Puspita_Period_Log, Indirani_A, Shweta, BORAN, PCOSGen, Anagha, ibadeus |

R1–R4 are scientific. R5–R6 are legal and statistical.

---

## 3. What survives

| collection | country | label source | licence | tier | records | positive | prevalence |
|---|---|---|---|---:|---:|---:|
| Kottarathil_full | India | clinical (Rotterdam, retrospective) | CC BY-NC-SA 4.0 | full corpus | 541 | 177 | 32.7% |
| Chaabouni | Tunisia | clinical (Rotterdam, case-control) | CC BY 4.0 | permissive | 88 | 45 | 51.1% |
| Gawron | Poland | clinical (explicit Rotterdam columns) | CC0 1.0 | permissive | 158 | 141 | 89.2% |
| Sahil_Koli | India | self-report survey | CC0 | permissive | 465 | 102 | 21.9% |
| hasaanrana | Pakistan | self-report survey | Other (unspecified) | fetch-only | 173 | 38 | 22.1% |
| **total** | **4 countries** | | | | **1,425** | **503** | **35.3%** |

**711 records** are permissively licensed (CC BY 4.0). **1,252** can be redistributed if
the corpus carries CC BY-NC-SA 4.0. **173** (hasaanrana) have no redistribution right and
ship as a loader.

A sixth collection, **Kurdistan** (Iraq, 242 records, 8 etiology classes after
whitespace normalisation, PCOS n=46), is
real and clean but answers a different question. It is held as a separate multi-class
track rather than folded into the binary core.

---

## 4. Files

```
harmonized/
  fetch.py                    retrieves the 6 sources, verifies SHA-256
  build_harmonized.py         the whole build; rerun to regenerate everything
  build_image_registry.py     image-side registry and exclusion reasons
  build_sources_manifest.py   regenerates manifest/sources.csv
  baseline_loco.py            the baseline: one model, one score per fold
  manifest/
    sources.csv               url, licence, sha256, retrieval method per source
  catalogue.csv               all 33 entries: verdict, decision, licence, tier
  licence_manifest.csv        what may be shipped vs fetched
  duplicate_registry.csv      every known redundancy relation, with the metric
  splits_loco.csv             leave-one-collection-out folds + inner 80/20 split
  baseline_loco_results.csv   the scores
  BUILD_REPORT.md             generated counts and findings
  images/
    image_registry.csv        13 image entries, decisions and reasons
    README.md                 why the image modality yields 295 images
  core/                       generated; gitignored
    core_records.csv          one row per patient: label, country, licence, source
    harmonized_long.csv       tidy: one row per (record, variable, value)
    harmonized_wide.csv       variables present in >=3 collections
    model_matrix.csv          wide minus all Rotterdam criterion variables
    kurdistan_etiology.csv    secondary track: 242 records, 8 classes
  sources/                    fetched source files; gitignored
```

### Rebuild from scratch

```powershell
uv run --with pandas --with openpyxl --with numpy python fetch.py
uv run --with pandas --with openpyxl --with numpy python build_harmonized.py
uv run --with pandas python build_image_registry.py
uv run --with pandas --with numpy --with scikit-learn python baseline_loco.py
```

`fetch.py --verify` checks what is already present without downloading.
`fetch.py --from-dir PATH` accepts files downloaded manually (needed for the two
Mendeley sources). Kaggle sources need the Kaggle CLI and credentials.

The repository does **not** contain the data. `core/`, `sources/` and
`_downloads/` are gitignored; committing them would publish the corpus, which
two source licences prohibit.

### Why long format is the primary table

Five collections share at most **10 of 41 measured variables**. A merge on all 41
would leave **55% of cells structurally empty** — and structural missingness is not
missing-at-random. `harmonized_long.csv` keeps every measured value with its original
unit, the conversion applied, and the source column, so nothing is silently lost:

| column | meaning |
|---|---|
| `record_id` | `<collection>-<row>`, stable across rebuilds |
| `variable` | canonical name, e.g. `testosterone_nmol_l` |
| `value_original`, `unit_original` | exactly as published |
| `value_canonical`, `unit_canonical` | after conversion |
| `conversion_factor` | 1.0 when no conversion |
| `source_column` | the literal header it came from |
| `criterion_leak` | 1 if the variable is a Rotterdam component |
| `plausible` | 0 if outside the physiological window |

Only **23 of 26,389 values (0.09%)** fall outside their window; they are kept in the long
file with `plausible=0` and set to NA in the wide matrix.

---

## 5. Splits: leave-one-collection-out

`random_state=20261110`.

| fold | train | test |
|---|---|---|
| Kottarathil_full | Chaabouni, Gawron, Sahil_Koli, hasaanrana | Kottarathil_full |
| Chaabouni | the other four | Chaabouni |
| Gawron | the other four | Gawron |
| Sahil_Koli | the other four | Sahil_Koli |
| hasaanrana | the other four | hasaanrana |

A row-level split would be the exact error this project documented: PCOSGen's official
train/test split overlaps by 63%. Splitting by collection is the only split that tests
what the field actually claims — that a PCOS model generalises across populations.

Within each training fold, `inner_split` gives an 80/20 stratified holdout.

### First result

`baseline_loco.py` — ExtraTrees on the eight non-criterion variables plus missingness
indicators, no tuning, no feature selection:

| held-out collection | n test | prevalence | AUROC |
|---|---:|---:|---:|
| Chaabouni | 88 | 51.1% | 0.675 |
| Gawron | 158 | 89.2% | 0.806 |
| Kottarathil_full | 541 | 32.7% | 0.587 |
| Sahil_Koli | 465 | 21.9% | 0.612 |
| hasaanrana | 172 | 22.1% | 0.698 |
| **mean** | | | **0.676** |

The published within-dataset accuracies for this field are above 95%. The same variables,
transferred across populations, reach **0.676**. That gap is the point of the dataset: it
is a benchmark for the claim the field makes, not another way to inflate it.

Gawron's 0.806 should be read with care — only 17 negatives, so its AUROC is unstable.

---

## 6. Licence tiers

CC BY-NC-SA **permits redistribution**. It is not a "no". It imposes three conditions:
attribution, non-commercial use, and ShareAlike — any adaptation must carry the same
licence. A harmonised corpus that pools these rows is an adaptation, so ShareAlike
propagates to the whole corpus.

That produces three release channels, not two:

| channel | collections | records | licence | commercial use |
|---|---|---:|---|---|
| **permissive core** | Chaabouni (CC BY 4.0), Gawron (CC0), Sahil_Koli (CC0) | 711 | CC BY 4.0 | yes |
| **full corpus** | + Kottarathil_full (CC BY-NC-SA 4.0) | 1,252 | CC BY-NC-SA 4.0 | no |
| **fetch-only** | hasaanrana (licence unspecified) | 173 | — | — |

**hasaanrana is the only genuine blocker.** "Other (specified in description)" is not a
licence grant; absent one, copyright defaults to all rights reserved. It ships as a loader
plus row hashes, or not at all until the author grants permission.

**Kottarathil must be cited exactly as the author requests:**

```bibtex
@misc{kottarathil2020pcos,
  author       = {Prasoon Kottarathil},
  title        = {Polycystic ovary syndrome (PCOS)},
  year         = {2020},
  publisher    = {Kaggle},
  howpublished = {\url{https://www.kaggle.com/prasoonkottarathil/polycystic-ovary-syndrome-pcos}},
  note         = {Licence: CC BY-NC-SA 4.0}
}
```

The author's note — *"I encourage you to use this Dataset to start your own projects"* —
is an encouragement to use, which the licence already grants. It does not add rights
beyond CC BY-NC-SA, and it does not waive ShareAlike.

**Practical consequence for the paper:** deposit the permissive core under CC BY 4.0 and
the full corpus under CC BY-NC-SA 4.0 as two Zenodo records, or one record with two
folders and a clear licence statement per folder. Do not merge them into a single
permissively licensed release — that would breach ShareAlike.

---

## 7. Known limitations

1. **Prevalence is not comparable across collections.** Gawron is an anovulation cohort
   (89% PCOS); Sahil Koli is a general self-report survey (22%). Pooling without weighting
   will bias any pooled estimate.
2. **Label ascertainment differs.** Three collections are clinician-diagnosed; two are
   self-report. A model cannot distinguish "PCOS" from "told I had PCOS".
3. **Only Gawron supports criterion-level supervision.** If you want OD/HA/PCOM labels,
   you have 158 records, not 1,425.
4. **The image modality contributes nothing to the binary core.** After global perceptual
   deduplication the image landscape is one pool plus residuals, and the detection
   collections carry object classes, not diagnosis.
5. **Kottarathil remains criterion-leaking** even though the leaking columns are withheld
   from `model_matrix.csv`: the label was assigned by clinicians who saw those columns.
   Withholding them removes the mechanical leak, not the ascertainment path.
6. **Four countries, five collections.** This is a transfer benchmark, not a
   representative sample of any population.

---

## 8. What this is not

- Not a claim that PCOS can be diagnosed from these variables.
- Not a replacement for external validation on a prospective cohort.
- Not a licence to redistribute **hasaanrana** values — that collection has no licence grant.
  Kottarathil may be redistributed, but only under CC BY-NC-SA 4.0.
- Not a merged image dataset. The image side is a manifest and an exclusion list.

---

## 9. Rebuild

```powershell
uv run --with pandas --with openpyxl --with numpy python Works\harmonized\build_harmonized.py
```

Deterministic: the only randomness is the split seed. Rebuilds reproduce every count in
`BUILD_REPORT.md`.

---

## 10. Findings this build surfaced

These were not visible in the atlas and are new contributions in their own right:

1. **Kottarathil's `Cycle length(days)` is period duration, not cycle length.** Values run
   2–12 days with mode 5; true cycle length is 21–35 days. Sahil Koli's period-duration
   column independently confirms it (mean 4.60 vs 4.94 days). Pooling the two naively
   would have produced a variable with no clinical meaning.
2. **Kottarathil's `RBS(mg/dl)` is a random blood sugar**, not fasting glucose. It cannot
   be pooled with the fasting glucose in Gawron and Chaabouni.
3. **Gawron's file contains two summary-statistic rows** appended after the patient rows.
   Read naively they become two patients, one with a "label" of 82. This also means the
   atlas's Gawron base rate (0.5125 = 82/160) was computed on 160 rows, not 158.
4. **hasaanrana's `Height_ft` is labelled feet but stores centimetres** (157.48, 165.1).
5. **Kottarathil's LH and FSH contain unit errors** (max 2,018 and 5,052 mIU/mL) and
   vitamin D reaches 6,014 ng/mL — 3 orders of magnitude out.

---

## 11. A note on the duplication test

`duplicate_registry.csv` records a coarse cross-collection check on `(age, BMI, label)`.
It finds a handful of collisions — 4 to 20 rows per pair, under 5% of the smaller
collection — and each is reported as **coincidental**. Three coarse fields cannot
establish record identity, and the collections have disjoint schemas, so exact row-level
matching is not testable across them.

The evidence that these five collections are independent is **provenance**, not row
matching: different countries, different recruitment frames, different label instruments,
different publication years, and no shared schema lineage. Where duplication *was*
testable — byte identity, row hashes, perceptual hashes — it was found and is recorded:
Indirani = ibadeus (0 MD5 mismatches), the Anagha/Shweta/BORAN pool (97–100% containment),
PCOSGen train/test (63.3%), Samiksha and Lucas (same generator, 0 shared rows).
