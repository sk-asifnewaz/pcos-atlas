# Handover: adding the verified core to Paper-1

**For:** the research-assistant agent editing `LaTeX/main.tex`
**From:** dataset build, `Works/harmonized/`
**Date:** 13 November 2026

**Repository:** https://github.com/sk-asifnewaz/pcos-atlas
(private until submission; make public before the paper goes out, then mint a
Zenodo DOI and replace the placeholder in the Data Availability section)

---

## 0. What this adds and why

Paper-1 currently audits 33 public PCOS dataset entries and concludes that the
public landscape is redundant and artefact-laden. It has no constructive half:
a reviewer will ask *"so what should anyone use instead?"*

This handover adds one section that answers that question — the subset that
survives the audit, expressed in one schema, plus the first cross-population
transfer measurement on it. It is **not** a data-release announcement. The data
is not redistributed (see `docs/DATA_AVAILABILITY.md`); the contribution is the
construction and the measurement.

**Do not change any existing number, table, figure or claim.** This is additive.

---

## 1. Source of truth for every number

Every figure below comes from files in `Works/harmonized/`. If a number is not in
this table, do not write it.

**Repository:** `https://github.com/sk-asifnewaz/pcos-atlas` — contains the code,
the source manifest with SHA-256 hashes, the 33-entry catalogue, the duplicate
registry, the LOCO splits, the image registry and the baseline. It does **not**
contain the data: `core/` and `sources/` are gitignored, because two source
licences prohibit redistribution.

| quantity | value | file |
|---|---:|---|
| catalogue entries | 33 | `catalogue.csv` |
| distinct collections | 27 | `TableS1_verification_atlas.csv` |
| collections passing all six rules | 7 (6 tabular, 1 image) | `catalogue.csv` |
| binary-label core collections | 5 | `catalogue.csv` |
| core patient records | 1,425 | `core/core_records.csv` |
| records with a usable label | 1,424 | `core/core_records.csv` |
| positive records | 503 (35.3%) | `core/core_records.csv` |
| measured variables | 41 | `core/harmonized_long.csv` |
| variables in ≥3 collections | 10 | `BUILD_REPORT.md` |
| values outside physiological window | 23 of 26,389 (0.09%) | `BUILD_REPORT.md` |
| permissively licensed records | 711 | `licence_manifest.csv` |
| full-corpus records | 1,252 | `licence_manifest.csv` |
| fetch-only records | 173 | `licence_manifest.csv` |
| mean LOCO AUROC | 0.676 | `baseline_loco_results.csv` |
| size-weighted LOCO AUROC | 0.638 | `baseline_loco_results.csv` |
| image entries retained | 1 (Borna, 295 images) | `images/image_registry.csv` |
| etiology track records | 242 (8 classes, 46 PCOS) | `core/kurdistan_etiology.csv` |

Per-collection counts (records / positive / prevalence):

| collection | country | label source | licence | n | pos | prev |
|---|---|---|---:|---:|---:|---:|
| Kottarathil_full | India | clinical (Rotterdam) | CC BY-NC-SA 4.0 | 541 | 177 | 32.7% |
| Chaabouni | Tunisia | clinical (Rotterdam) | CC BY 4.0 | 88 | 45 | 51.1% |
| Gawron | Poland | clinical (Rotterdam) | CC0 1.0 | 158 | 141 | 89.2% |
| Sahil_Koli | India | self-report | CC0 | 465 | 102 | 21.9% |
| hasaanrana | Pakistan | self-report | unspecified | 173 | 38 | 22.1% |

LOCO per fold: Chaabouni 0.675 (n=88), Gawron 0.806 (n=158),
Kottarathil 0.587 (n=541), Sahil Koli 0.612 (n=465), hasaanrana 0.698 (n=172).

---

## 2. Change 1 — revise the scope statement

`main.tex` line ~107. The current text promises *"no model accuracy"*, which the
new section breaks. Replace:

```latex
\noindent\textbf{Scope statement.}
This paper reports \emph{no model accuracy}. It is a catalogue and a fitness-for-use
audit. Where a quantity called \AUROC{} appears in our results it is a
\textbf{diagnostic probe computed by us to detect artefacts}, not a claim about
diagnostic performance; a \emph{high} value is a warning.
```

with:

```latex
\noindent\textbf{Scope statement.}
This paper reports \emph{no diagnostic accuracy}. It is a catalogue, a
fitness-for-use audit, and a transfer benchmark. Where a quantity called \AUROC{}
appears in our results it is either a \textbf{diagnostic probe computed by us to
detect artefacts} or a \textbf{transfer measurement on the verified core}; neither
is a claim about diagnostic performance. For the probes a \emph{high} value is a
warning; for the transfer measurement a \emph{low} value is the expected result.
```

---

## 3. Change 2 — insert a new Section 5

Insert **after** the last Results subsection (the Li et al.\ taxonomy bridge,
`\label{sec:taxonomy-results}`) and **before** `\section{Discussion}`.

Renumbering is automatic if the paper uses `\ref`; check that no `\section`
number is hard-coded in prose.

```latex
% ================================================================
\section{A verified core and a transfer benchmark}
\label{sec:core}

\subsection{Six rules for inclusion}

The audit above is diagnostic. This section is the constructive half: what
remains of the 33 entries once every entry that fails a provenance test is
removed, and what that residue can support. A collection enters the verified core
only if it passes six rules, each enforced in code rather than asserted in prose:
an independent label (the target is not a function of a Rotterdam input); no
tautology (no single input at purity 1.000); no synthetic construction
(documented or by AND-rule signature); no corrupted values; a licence that
permits redistribution; and no duplication, subset or companion-table
relationship to another included collection. The rules are stated in full in the
deposited documentation, together with the entry each one rejects.

\subsection{What survives}

Six tabular collections pass. Five carry a binary diagnosis label and form the
core; the sixth is an etiology cohort that answers a different question and is
held separately (Table~\ref{tab:core}). We refer to the resulting corpus as
\textbf{PCOS-ATLAS}; the verification atlas of Section~\ref{sec:collapse} remains
the audit table, and the two should not be conflated. The core contains
\textbf{1,425 patient records} from four countries, of which 1,424 carry a
usable label and 503 (35.3\%) are positive.

\begin{table}[H]
\centering
\caption{The verified core. Prevalence is the positive fraction of labelled
records within each collection.}
\label{tab:core}
\small
\begin{tabular}{@{}llllrrr@{}}
\toprule
Collection & Country & Label source & Licence & Records & Positive & Prevalence \\
\midrule
\ds{Kottarathil} & India     & clinical    & CC BY-NC-SA 4.0 & 541 & 177 & 32.7\% \\
\ds{Chaabouni}    & Tunisia   & clinical    & CC BY 4.0       &  88 &  45 & 51.1\% \\
\ds{Gawron}       & Poland    & clinical    & CC0 1.0         & 158 & 141 & 89.2\% \\
\ds{Sahil\_Koli}  & India     & self-report & CC0             & 465 & 102 & 21.9\% \\
\ds{hasaanrana}   & Pakistan  & self-report & unspecified     & 173 &  38 & 22.1\% \\
\midrule
Total & 4 countries & & & \textbf{1,425} & \textbf{503} & \textbf{35.3\%} \\
\bottomrule
\end{tabular}
\end{table}

The core is small, and its smallness is the result rather than a limitation of
the search. Of the 41 variables measured across the five collections, only ten
appear in three or more; a merge on all 41 would leave 55\% of cells
structurally empty, and structural missingness is not missing at random. We therefore express the corpus in long format, one row per
(record, variable), retaining the original value, the original unit, the
conversion applied and the source column, so that no value is silently
transformed.

Harmonising the five surfaced five metadata errors that the audit alone did not
detect. \ds{Kottarathil}'s \ds{Cycle length(days)} holds period duration (2--12
days, mode 5), not cycle length (21--35 days); \ds{Sahil\_Koli}'s period-duration
column independently confirms the interpretation (mean 4.60 vs.\ 4.94 days).
\ds{Kottarathil}'s \ds{RBS(mg/dl)} is a random blood sugar, not fasting glucose,
and cannot be pooled with the fasting values in \ds{Gawron} and \ds{Chaabouni}.
\ds{Gawron}'s workbook ends with two summary-statistic rows which, read naively,
become two patients --- one with a ``label'' of 82. \ds{hasaanrana}'s
\ds{Height\_ft} is labelled in feet but stores centimetres. And
\ds{Kottarathil}'s LH and FSH contain unit errors reaching 2{,}018 and 5{,}052
mIU/mL, with vitamin D reaching 6{,}014 ng/mL. Twenty-three of 26{,}389 values
(0.09\%) fall outside a physiological window and are withheld from the modelling
matrix.

The image modality contributes no records to the core. Of thirteen image
entries, eight are duplicates, sourcing artefacts or not PCOS, and four are
detection collections whose bounding-box class identifiers denote object classes
(follicle, ovary) rather than diagnosis. One collection survives --- 295 images
in three classes with no cross-split or cross-dataset overlap --- which is a
validation set, not a corpus.

\subsection{Transfer across populations}

Because the five collections come from four countries and use two different
label instruments, the only defensible split is by collection. We therefore
report leave-one-collection-out transfer: train on four, test on the fifth
(Table~\ref{tab:loco}). The model is a five-fold \texttt{ExtraTrees} classifier
on the eight non-criterion variables plus explicit missingness indicators, with
no tuning and no feature selection. Rotterdam criterion variables are withheld
from the feature matrix.

\begin{table}[H]
\centering
\caption{Leave-one-collection-out transfer. One model, one score per fold, no
tuning.}
\label{tab:loco}
\begin{tabular}{@{}lrrr@{}}
\toprule
Held-out collection & $n$ & Prevalence & \AUROC{} \\
\midrule
\ds{Chaabouni}    &  88 & 51.1\% & 0.675 \\
\ds{Gawron}       & 158 & 89.2\% & 0.806 \\
\ds{Kottarathil}  & 541 & 32.7\% & 0.587 \\
\ds{Sahil\_Koli}  & 465 & 21.9\% & 0.612 \\
\ds{hasaanrana}   & 172 & 22.1\% & 0.698 \\
\midrule
Mean & & & \textbf{0.676} \\
\bottomrule
\end{tabular}
\end{table}

The same variables that separate cases from controls within a dataset --- where
the published literature reports accuracies above 95\% --- reach a mean \AUROC{}
of \textbf{0.676} when transferred across populations. The size-weighted mean is
0.638. \ds{Gawron}'s 0.806 should be read with care: only seventeen of its 158
records are negative, so its fold estimate is unstable.

\subsection{What the core can and cannot support}

The core supports three uses and no others. It supports \emph{benchmarking
transfer}: a fixed, provenance-verified, de-duplicated set on which a model's
cross-population behaviour can be measured rather than asserted. It supports
\emph{methodological work} on label noise, missingness and dataset shift, because
the label instrument is documented per collection. And it supports
\emph{criterion-level supervision} on \ds{Gawron} alone, which is the only
collection carrying explicit Rotterdam criterion columns.

It cannot support a claim of diagnostic performance. Prevalence ranges from 22\%
to 89\% across collections, two of the five labels are self-reported rather than
clinically ascertained, and the collections differ in era, setting and
recruitment frame. A pooled estimate from this corpus is a statement about a
mixture, not about a population.
```

---

## 4. Change 3 — Data Availability

Replace the body of `\section*{Data Availability}` (lines 2208–2227) with the
text in `docs/DATA_AVAILABILITY.md`. Keep `\label{sec:data}`. The repository URL
is already in the text; the only placeholder left is
`[repository DOI to be inserted]`.

---

## 5. Change 4 — one sentence in the abstract

In the abstract's Results paragraph, after the sentence about informative
missingness (currently ending *"too few missing values to test it."*), add:

```latex
\textbf{(6) The surviving subset is small and transfers poorly.} Six collections
pass all six provenance rules, five of them forming a 1,425-record core across
four countries; the variables that separate cases within a dataset reach a mean
\AUROC{} of only 0.676 when transferred across populations.
```

In the Conclusions, append to the final sentence:

```latex
We provide a per-dataset transfer-risk tier, an informativeness statement, a
pre-training reporting checklist, and a verified core on which cross-population
transfer can be measured.
```

---

## 6. Change 5 — references

`references.bib` now contains five dataset citations (`kottarathil2020`,
`chaabouni2022`, `gawron2025`, `koli2023`, `hasaanrana2024`). They are currently
uncited, so BibTeX will drop them. Cite each collection by name at first mention
in Section~\ref{sec:core} — e.g.\ ``\ds{Kottarathil} \citep{kottarathil2020}''.
Attribution is a licence condition for the CC BY and CC BY-NC-SA sources, not a
courtesy.

---

## 7. Do not

1. **Do not describe this as a released dataset.** The data is not distributed.
   It is a verified core, reconstructed by a loader. Wording matters here.
2. **Do not add any accuracy, F1, sensitivity or AUC other than Table 3.** The
   paper's whole argument is that such numbers are not comparable across these
   datasets.
3. **Do not call 0.676 a failure.** It is the expected result and the point of
   the section. Frame it as the ceiling that the field's claims must be measured
   against.
4. **Do not merge the core with the atlas.** `TableS1` is the audit result; the
   core is the usable residue. Two artifacts, two purposes.
5. **Do not round 1,425 to "about 1,400"** or otherwise soften it. The exact
   number is the finding.
6. **Do not cite the etiology cohort as part of the core.** It is a separate
   track (242 records, 8 classes, 46 PCOS) and is mentioned only in passing.

---

## 8. Before you hand it back

- [ ] `pdflatex → bibtex → pdflatex → pdflatex` compiles with no undefined refs
- [ ] every number in the new section matches §1 of this document
- [ ] `\ref{tab:core}`, `\ref{tab:loco}` and `\ref{sec:core}` resolve
- [ ] the scope statement no longer promises "no model accuracy"
- [ ] the five dataset citations appear in the bibliography
- [ ] the Data Availability DOI placeholder is the only remaining TODO
