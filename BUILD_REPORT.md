# PCOS-HARM build report

Built from 33 catalogue entries.

## What survives

- **5 collections** pass all six inclusion rules.
- **1425 patient records**, of which **1424** carry a usable binary label (503 positive, 35.3%).

### Release tiers

- **Permissive core** — 711 records (288 positive), CC BY 4.0. Chaabouni + Gawron + Sahil_Koli. Commercial reuse allowed.
- **Full corpus** — 1252 records (465 positive), CC BY-NC-SA 4.0. Adds Kottarathil_full (541 records). ShareAlike forces the whole harmonised corpus to carry the same licence.
- **Fetch-only** — 173 records (hasaanrana): licence unspecified, so no redistribution right exists. Ship loader + row hashes.

- **23 values** were outside the physiological window and are set to NA in the wide matrix (0.09% of all values).

## Per-collection yield

| collection | country | label source | licence | tier | records | positive | prevalence | implausible values |
|---|---|---|---|---|---:|---:|---:|---:|
| Kottarathil_full | India | clinical (Rotterdam, retrospective) | CC BY-NC-SA 4.0 | noncommercial_sharealike | 541 | 177 | 32.7% | 17 |
| Chaabouni | Tunisia | clinical (Rotterdam, case-control) | CC BY 4.0 | permissive | 88 | 45 | 51.1% | 1 |
| Gawron | Poland | clinical (explicit Rotterdam criterion columns) | CC0 1.0 | permissive | 158 | 141 | 89.2% | 2 |
| Sahil_Koli | India | self-report survey | CC0 | permissive | 465 | 102 | 21.9% | 3 |
| hasaanrana | Pakistan | self-report survey | Other (unspecified) | unknown_do_not_redistribute | 173 | 38 | 22.1% | 0 |

## Variable coverage (collections per variable)

| variable | collections | criterion leak |
|---|---:|---|
| bmi | 5 | no |
| age_years | 4 | no |
| height_cm | 4 | no |
| weight_kg | 4 | no |
| cycle_irregular | 3 | yes |
| fsh_miu_ml | 3 | no |
| hirsutism | 3 | yes |
| vitd_ng_ml | 3 | no |
| prolactin_ng_ml | 3 | no |
| lh_miu_ml | 3 | no |
| estradiol_pmol_l | 2 | no |
| tsh_miu_l | 2 | no |
| chol_total_mmol_l | 2 | no |
| amh_ng_ml | 2 | no |
| acne | 2 | no |
| dbp_mmhg | 2 | no |
| fast_food | 2 | no |
| homa_ir | 2 | no |
| period_duration_days | 2 | no |
| skin_darkening | 2 | no |
| sbp_mmhg | 2 | no |
| hair_loss | 2 | no |
| hdl_mmol_l | 2 | no |
| glucose_fasting_mmol_l | 2 | no |
| ldl_mmol_l | 2 | no |
| weight_gain | 2 | no |
| trig_mmol_l | 2 | no |
| waist_cm | 2 | no |
| testosterone_nmol_l | 2 | yes |
| regular_exercise | 2 | no |
| cycle_length_days | 1 | yes |
| glucose_random_mg_dl | 1 | no |
| fg_score | 1 | yes |
| insulin_uiu_ml | 1 | no |
| hip_cm | 1 | no |
| follicle_r_n | 1 | yes |
| family_history | 1 | no |
| follicle_l_n | 1 | yes |
| ovary_vol_r_ml | 1 | yes |
| pcom | 1 | yes |
| ovary_vol_l_ml | 1 | yes |

## Wide core: 10 variables present in >=3 collections

Variables: `bmi`, `age_years`, `height_cm`, `weight_kg`, `cycle_irregular`, `fsh_miu_ml`, `hirsutism`, `vitd_ng_ml`, `prolactin_ng_ml`, `lh_miu_ml`

## Findings surfaced by this build

- 2 row(s) dropped for a non-binary label (Gawron) - summary-statistic rows embedded in the source file
- Kottarathil `RBS(mg/dl)` is a **random** blood sugar, not fasting. It is mapped to `glucose_random_mg_dl` and is therefore not poolable with Gawron/Chaabouni fasting glucose.
- Kottarathil `Cycle length(days)` holds **period/flow duration** (2-12 days, mode 5), not cycle length (21-35 days). Remapped to `period_duration_days`; pooling it with Gawron's 30-55 day cycle length would have corrupted the variable. Sahil Koli's period-duration column independently confirms the interpretation (mean 4.60 vs 4.94 days).
- hasaanrana `Height_ft` is labelled feet but holds centimetres (157.48, 165.1). Mapped as cm; BMI derived from it agrees with the stated range.
- Kottarathil follicle counts and ovary volumes are Rotterdam components. They are kept in the long file with `criterion_leak=1` and withheld from `model_matrix.csv`.
- Only Gawron carries explicit criterion columns, so it is the only collection where criterion-level (OD/HA/PCOM) supervision is possible.
- Gawron is an **anovulation cohort**, not a general-population case-control: 141 of 158 records are PCOS. It will dominate the positive class in any pooled analysis.