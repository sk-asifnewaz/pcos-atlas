# Data Availability — replacement text

**Repository:** https://github.com/sk-asifnewaz/pcos-atlas (currently private —
flip to public at submission, then mint the Zenodo DOI).

Replace the body of `\section*{Data Availability}` in `LaTeX/main.tex`
(currently lines 2208–2227) with the block below. Keep the `\label{sec:data}`.

The bracketed DOI is the only thing that must be filled in before submission.

```latex
\section*{Data Availability}
\label{sec:data}

All source datasets analysed here are publicly downloadable from their original
hosts. \textbf{No source data are redistributed in this work.} Two of the five
collections that form the verified core carry licences that prohibit it: the
Kottarathil collection is licensed CC BY-NC-SA 4.0, whose ShareAlike clause would
propagate to any harmonised derivative, and the hasaanrana collection states no
licence at all, so no redistribution right exists.

We therefore deposit the \emph{construction} rather than the data: the
harmonisation code, a source manifest recording the URL, stated licence and
SHA-256 of every source file, the exclusion catalogue for all 33 entries, the
duplicate registry, the leave-one-collection-out split definitions, and the
baseline. The deposit is archived at \textbf{[repository DOI to be inserted]};
the development version is at
\url{https://github.com/sk-asifnewaz/pcos-atlas}.

\texttt{fetch.py} retrieves each source from its publisher and verifies it
against the recorded SHA-256 before the build proceeds; a source that has been
silently updated fails the check rather than producing a different corpus.
\texttt{build\_harmonized.py} then regenerates every table and figure in this
paper from those verified files. The master verification atlas
(\texttt{TableS1\_verification\_atlas.csv}), the per-modality audit tables,
per-file MD5 and perceptual hashes, and the catalogue workbooks are included in
the same deposit.

Datasets are referred to throughout by their catalogue name, which is the public
identifier under which they are distributed. Where a finding characterises a named
dataset, it characterises \emph{the version downloaded at the time of audit}; the
per-file hashes in the deposit allow any later version to be distinguished. We
describe properties of the data as we found them and make no claim about the
intentions or competence of the individuals who uploaded them.
```

## Why this wording

- It states the constraint **once, factually**, and then moves on. No apology.
- It names the two licences, so an editor can check the claim.
- It puts the reproducibility burden on hashes rather than on trust.
- It keeps the existing paragraph about catalogue names and versions, which is
  already good and should not be lost.

## If a reviewer asks for deposited data

Do not rewrite the section. Add one sentence and, if the editor insists, deposit
the permissive subset only (Chaabouni + Gawron + Sahil Koli, 711 records,
CC BY 4.0 — legally clean because those three sources are CC BY and CC0). The
build already tags every record with its licence tier, so producing that subset
is one filter, not a rewrite. See `licence_manifest.csv`.
