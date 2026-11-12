# Image track

The image modality is **not** part of the binary core. This folder records why,
so the exclusion is auditable rather than asserted.

- catalogue entries: **13**
- retained as a clean classification set: **1** (295 unique images)
- detection-only (no diagnosis label): **4**
- excluded (duplicate, artefact, or not PCOS): **8**

## Why the image side yields almost nothing

1. **One pool, many names.** Anagha_Choudhari, Shweta_2000 and BORAN_TOKTAY are one
   image pool presented three ways (97.3-100% containment). ibadeus and Indirani_A are
   byte-identical across all 11,784 files. PCOSGen_train is 88.9% contained in ibadeus.
2. **Detection is not diagnosis.** researchworks, Busakorn, VanessaS and impro_yvqsf
   carry YOLO boxes whose class ids are object classes (follicle, ovary), not PCOS
   status. They cannot be converted into a classification label without inventing one.
3. **What is left is small.** After excluding the pool, the duplicates and the
   detection sets, the only clean independent classification collection is **Borna**:
   295 unique images, 3 classes (Normal / Dominant_Follicle / PCO), 0 cross-split leakage, 0 cross-dataset overlap.

That is a validation set, not a corpus. Adding it to PCOS-ATLAS would not strengthen
the dataset; it would invite the objection that the image half is decorative.

## Retained

- **Borna** - 295 unique images, classification, CC BY 4.0 License.

## Excluded

| dataset | images | unique after dedup | licence | reason |
|---|---:|---:|---|---|
| Anagha_Choudhari | 3856 | 3856 | Unknown | sourcing artefact (metadata AUROC 1.000); hub of the shared image pool |
| BORAN_TOKTAY | 1924 |  | Unknown | 100% contained in Anagha_Choudhari; inverted label semantics |
| Indirani_A | 11784 |  | CC BY 4.0 | byte-identical duplicate of ibadeus (0 MD5 mismatches) |
| MMOTU | 6556 |  | Apache-2.0 license | ovarian tumour segmentation, not PCOS |
| PCOSGen_test | 1468 | 903 | Creative Commons Attribution 4.0 International | 63.28% overlap with PCOSGen_train; 58.45% inside ibadeus |
| PCOSGen_train | 3200 | 1760 | Creative Commons Attribution 4.0 International | 88.88% of its images are found inside ibadeus |
| Shweta_2000 | 1987 | 1755 | Unknown | 97.28% of its images are contained in Anagha_Choudhari |
| ibadeus | 11784 | 2454 | CC0: Public Domain | sourcing artefact; Grad-CAM on ruler overlay; byte-identical to Indirani_A |

## Detection-only

| dataset | images | unique after dedup | licence |
|---|---:|---:|---|
| Busakorn | 954 | 411 | CC BY 4.0 |
| VanessaS | 1363 | 1181 | Public Domain |
| impro_yvqsf | 302 | 297 | CC BY 4.0 |
| researchworks | 5437 | 5256 | CC BY 4.0 |