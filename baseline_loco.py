#!/usr/bin/env python
"""
PCOS-ATLAS baseline: leave-one-collection-out transfer.
One model, one task, one score per fold. No tuning, no feature selection.

Features are the non-criterion variables in core/model_matrix.csv plus explicit
missingness indicators (structural missingness is informative - Kataryńczuk 2026).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline

HERE = Path(__file__).resolve().parent
m = pd.read_csv(HERE / "core" / "model_matrix.csv")

feat = [c for c in m.columns if c not in ("record_id", "collection", "label_pcos", "country")]
X = m[feat].copy()
# missingness indicators
for c in feat:
    X[f"{c}__isna"] = X[c].isna().astype(int)

m = m[m["label_pcos"].notna()].copy()
X = X.loc[m.index]
y = m["label_pcos"].astype(int).to_numpy()

rows = []
for coll in sorted(m["collection"].unique()):
    te = (m["collection"] == coll).to_numpy()
    tr = ~te
    if len(np.unique(y[tr])) < 2 or len(np.unique(y[te])) < 2:
        continue
    pipe = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("clf", ExtraTreesClassifier(n_estimators=400, min_samples_leaf=5,
                                     random_state=20261110, n_jobs=-1)),
    ])
    pipe.fit(X[tr], y[tr])
    p = pipe.predict_proba(X[te])[:, 1]
    rows.append(dict(fold=coll, n_train=int(tr.sum()), n_test=int(te.sum()),
                     prevalence_test=float(y[te].mean()),
                     auroc=roc_auc_score(y[te], p)))

res = pd.DataFrame(rows)
res.to_csv(HERE / "baseline_loco_results.csv", index=False)

print(res.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print(f"\nmean AUROC across folds: {res['auroc'].mean():.3f}")
print(f"weighted by test size:   {np.average(res['auroc'], weights=res['n_test']):.3f}")
