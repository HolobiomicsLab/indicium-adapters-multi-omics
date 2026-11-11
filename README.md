# indicium-adapters-multi-omics

A `multi-omics` `DomainAdapter` for the [indicium](https://github.com/HolobiomicsLab/indicium)
ecosystem: classification vocabulary and claim/ontology enrichment for
integration across two or more omics layers.

It owns **tier-3 concerns only** (ADR 0001): the classification vocabulary and
claim/ontology enrichment. It does **not** scan article text for repository
accessions — that is the canonical `accession_scanner` in `asb-domain-core`,
and a second copy of those patterns here would be the duplicate-then-drift
failure ADR 0001 exists to prevent. What this package contributes for
identifiers is the prefix table that *expands* accessions and ontology
CURIEs a consumer already holds.

## What the field is

Multi-omics is defined by integration, not by any one layer's biology: joint
dimensionality reduction, factor models, network fusion, cross-layer
correlation, imputation of a layer that is missing for some samples, and the
batch/normalisation problems that only appear once several layers are
combined. A multi-omics paper's distinctive claims say *which* layers were
combined, *how*, whether the layers were profiled on the same samples or only
matched across cohorts, what was normalised or batch-corrected, which layer
was predicted from which, and how the integration itself was validated. The
24 qualifiers below are organised around exactly those six questions.

## What it contributes

| Attribute | Source |
|---|---|
| `primary_domain` | `multi-omics` — without this, a multi-omics paper classifies as `other` in AgenticScienceBuilder |
| `subdomains` | the omics layers a paper can say it integrated (genomics, proteomics, metabolomics, …), read from EDAM's own children of *Omics* |
| `techniques` | integration methods (dimensionality reduction, network analysis, imputation, and their EDAM children), read from a second group of EDAM roots — see below |
| `qualifiers` | 24 snake_case qualifiers covering the layers combined, the integration method, pairing/matching design, normalisation and batch correction, cross-layer prediction, and validation |
| `ontology_prefixes` | prefix → base IRI: EDAM, OBI, EFO, GO, NCBITaxon, CHEBI, UBERON (ontologies), and PRIDE, MetaboLights, GEO, ArrayExpress (repository namespaces, expansion only) |
| `enrich_claim` | exact-match EDAM label lookup, one pass |

## Why the vocabulary needed two groups of EDAM roots

EDAM's *Multiomics* topic (`topic_4021`) is a leaf — it has no subclasses of
its own. Its parent, *Omics* (`topic_3391`), files every single-omics topic as
a direct child (Genomics, Proteomics, Metabolomics, Phenomics, Molecular
evolution, Fluxomics, Immunomics, Exposomics), and that is exactly the layer
vocabulary a multi-omics paper needs — so `subdomains` reads those eight terms
straight off EDAM (the *Omics* root itself and *Multiomics*, which EDAM also
files as one of *Omics*'s children, are both excluded: neither is a layer a
paper integrates).

But neither root reaches a vocabulary for the *methods* that combine layers,
because *Omics* files the layers being combined, not what combines them. So
`techniques` is read from a second, disjoint group of EDAM operation roots —
*Dimensionality reduction*, *Network analysis*, *Imputation* — chosen because
they are EDAM's own filing for this field's constitutive methods (see "What
the field is", above). `data/build_edam_index.py` records why two other
candidates, *Clustering* and *Data integration and warehousing*, were
considered and rejected: the former's children span domains as unrelated as
document clustering, and the latter is a leaf with nothing under it to
collect. Nothing here is hand-listed; both properties are read off the
generated index, and a test binds every subdomain and technique back to a
concept the index can resolve.

## This domain overlaps every single-omics domain, by construction

A paper integrating transcriptomics and proteomics genuinely uses
transcriptomics' and proteomics' own words to say what it integrated. A term
this adapter resolves therefore very often *also* resolves under the
genomics, transcriptomics or metabolomics adapter — several adapters walk
overlapping parts of the EDAM graph, and `Genomics` (`edam:topic_0622`) is a
true label for the text "genomics" no matter which adapter looked it up.

That CURIE is not wrong. What it is *not* is strong evidence, on its own, that
the paper meant the multi-omics sense rather than the single-layer sense —
disambiguating sense is not `enrich_claim`'s job; it resolves text to CURIEs
and stops there. A consumer running several domain adapters together, or a
downstream reader of `ontology_terms`, should weigh a match this adapter alone
produced differently from one several domain adapters agree on. The class
docstring on `MultiOmicsAdapter` says this again, next to the code it applies
to.

## Enrichment is exact-match, single pass

`enrich_claim` walks the `subject`, `object` and `qualifier` slots and resolves
each against the vendored EDAM index with `semapv:LexicalMatching` as the
justification. Substring and fuzzy matching over an ontology manufacture
confident-looking wrong CURIEs ("Omics" inside "Multiomics"), and a wrong
identifier is worse than no identifier. A slot that carries text but resolves
to nothing is recorded under `ontology_terms_unmatched` rather than passed
over, so "not an EDAM concept" stays distinguishable from "no attempt was
made". A slot another adapter already resolved is left untouched.

```python
from indicium_adapters_multi_omics import MultiOmicsAdapter

adapter = MultiOmicsAdapter()
adapter.enrich_claim({"subject": "Genomics", "qualifier": "integrated_by", "object": "MOFA+"})
# {'subject': 'Genomics', 'qualifier': 'integrated_by', 'object': 'MOFA+',
#  'ontology_terms': {'subject': 'edam:topic_0622'},
#  'ontology_term_justifications': {'subject': 'semapv:LexicalMatching'},
#  'ontology_terms_unmatched': {'object': 'MOFA+'}}
```

`MOFA+` stays unmatched here on purpose: it is a real, well-known tool, but it
is not an EDAM concept, and inventing a CURIE for it would be exactly the
wrong-identifier failure this package exists to avoid. Tool and method names
belong in the claim text itself, resolved by the qualifier that names them
(`integrated_by`), not by a manufactured ontology term.

## What this package does NOT do

- No accession recognition (ADR 0001) — SRA, PRIDE, MetaboLights, GEO and
  ArrayExpress accessions in article text are `asb-domain-core`'s concern.
- No sense disambiguation between "this is the multi-omics sense of Genomics"
  and "this is the single-layer sense" — see above.
- No curated technique vocabulary beyond what EDAM itself files under the
  roots recorded in `data/build_edam_index.py`. Widely-used integration tools
  and methods that EDAM does not carry as a concept (MOFA+, DIABLO, Seurat's
  WNN, mixOmics) are named through the `integrated_by` / `fused_by` /
  `factorized_by` qualifiers, as claim text, not as ontology terms.

## Install

The public dependencies are installed from PyPI with the development extra:

```bash
python -m pip install -e ".[dev]"
```

The `indicium.adapters` entry point makes it discoverable via
`indicium_adapters.discover_adapters()` on install — no configuration.

## Regenerating the bundled index

```bash
python -m indicium_adapters_multi_omics.data.build_edam_index
```

Reads EDAM through EBI OLS4, records the roots it was cut from, and emits the
`subtopics` (subdomains) and `techniques` lists off the same walk. Regenerate
on an EDAM release. Never runs at install or import time.

## Licence

MIT.
