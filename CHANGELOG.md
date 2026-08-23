# Changelog

All notable changes to **indicium-adapters-multi-omics** are documented in this file.
Format: [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/); versioning:
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Dates are ISO-8601.

## [0.1.0] — 2026-08-24

Initial release.

### Added
- `MultiOmicsAdapter` (`api_version=1`), registered on the `indicium.adapters` entry
  point. Declares `domain_id` / `primary_domain` = `multi-omics`, 24 snake_case domain
  qualifiers covering the layers combined, the integration method, pairing/matching
  design, normalisation and batch correction, cross-layer prediction, and validation.
- Vendored EDAM index cut from two disjoint root groups: `subdomains` (8 terms) reads
  the omics layers filed directly under EDAM's *Omics* (`topic_3391`), excluding
  *Omics* itself and *Multiomics* (which EDAM also files as a child of *Omics*, but
  which is the field's own name, not a layer it integrates); `techniques`
  (12 terms) reads a second group of EDAM operation roots — *Dimensionality
  reduction*, *Network analysis*, *Imputation* — chosen because neither the domain
  root (*Multiomics*, `topic_4021`, a leaf) nor *Omics* files the methods that combine
  layers. Both are read from the generated index, never hand-listed; see
  `data/build_edam_index.py` for the full root selection and the two candidates
  (*Clustering*, *Data integration and warehousing*) that were considered and
  rejected.
- `enrich_claim`: single-pass exact-match EDAM concept enrichment over the `subject`,
  `object` and `qualifier` slots, with `semapv:LexicalMatching` justification. Pure:
  returns a new dict and never overwrites a term another adapter has set.
- `ontology_terms_unmatched`: a slot that carried text but resolved to nothing, so a
  miss stays distinguishable from "not attempted".
- README documents that this domain overlaps every single-omics domain by
  construction, and that a match this adapter alone produces is weak, not wrong,
  evidence that the multi-omics sense rather than a single layer's sense was meant.

### Deliberately not included
- **Accession recognition.** Under ADR 0001 the canonical accession table in
  `asb-domain-core` owns those patterns. A test greps this package's own source and
  fails if an accession shape appears.
- **A curated technique list beyond what EDAM's own roots carry.** Widely-used tools
  the ontology does not model as a concept (MOFA+, DIABLO, mixOmics, Seurat's WNN)
  are named through qualifiers, as claim text, rather than invented as ontology terms.

### Known limitations
- Matching is exact after case-folding and whitespace collapse, so a paraphrase does
  not resolve. Substring or fuzzy matching over an ontology produces confident wrong
  CURIEs, and a wrong identifier is worse than none.
- The EDAM footprint of this domain is small (77 label/synonym entries) because
  *Multiomics* is a leaf in EDAM and its parent's technique vocabulary has to be
  sourced from elsewhere in the graph. Most of a multi-omics claim's specificity is
  expected to live in the 24 qualifiers and in claim text, not in matched ontology
  terms.
