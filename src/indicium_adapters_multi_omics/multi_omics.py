"""MultiOmicsAdapter -- the multi-omics DomainAdapter (api_version=1)."""

from __future__ import annotations

from typing import Final

from . import _edam

# Claim slots worth resolving against the EDAM index. ``qualifier`` is included
# because a qualifier literal sometimes carries a layer or technique name (a
# claim might record "genomics" or "network analysis" as its qualifier text
# before this adapter's own vocabulary is substituted in), which is itself an
# EDAM concept.
_ENRICHABLE_SLOTS: Final[tuple[str, ...]] = ("subject", "object", "qualifier")

# SSSOM justification for a label / synonym string match. Every CURIE this
# adapter emits comes from exact-after-normalisation matching against the
# vendored EDAM index, so this is the only justification it can honestly claim.
_LEXICAL: Final[str] = "semapv:LexicalMatching"

# Ontology vocabularies claim text is resolved against, or that a consumer may
# need to expand a term this adapter did not itself mint.
_ONTOLOGY_PREFIXES: Final[dict[str, str]] = {
    # The concept spine.
    "edam": _edam.EDAM_PREFIX,
    "OBI": "http://purl.obolibrary.org/obo/OBI_",
    "EFO": "http://www.ebi.ac.uk/efo/EFO_",
    "GO": "http://purl.obolibrary.org/obo/GO_",
    "NCBITaxon": "http://purl.obolibrary.org/obo/NCBITaxon_",
    "CHEBI": "http://purl.obolibrary.org/obo/CHEBI_",
    "UBERON": "http://purl.obolibrary.org/obo/UBERON_",
    # Repository namespaces this adapter does NOT mine from prose but whose
    # CURIEs a consumer may need to expand. Recognition of the accessions
    # themselves lives in asb-domain-core's canonical accession table (ADR 0001).
    "PRIDE": "https://identifiers.org/pride.project:",
    "MetaboLights": "https://identifiers.org/metabolights:",
    "GEO": "https://identifiers.org/geo:",
    "ArrayExpress": "https://identifiers.org/arrayexpress:",
}


class MultiOmicsAdapter:
    """Integration across two or more omics layers.

    Owns the tier-3 concerns only (ADR 0001): the classification vocabulary and
    claim/ontology enrichment. It deliberately does **not** recognise repository
    accessions -- those belong to the canonical accession table in
    ``asb-domain-core``, and a second copy of those patterns here would be the
    duplicate-then-drift failure ADR 0001 exists to prevent. What this adapter
    contributes for identifiers is ``ontology_prefixes``, so a consumer can
    expand the CURIEs that tier produces.

    The field this adapter models is integration itself: joint dimensionality
    reduction and factor models, network fusion, cross-layer correlation,
    imputation of a missing layer, and the batch and normalisation problems
    that appear only once layers are combined. Its distinctive claims name
    *which* layers were integrated and *how* -- not the biology any one layer
    already describes on its own, which is the sibling single-omics adapters'
    concern.

    ``subdomains`` and ``techniques`` are declared literally, as fixed by the
    2026-08-25 cross-domain vocabulary audit. They were previously read off the
    generated EDAM index; the audit's terms name no EDAM concept, so the index
    can no longer source them. The index still backs ``enrich_claim``.

    This domain overlaps every single-omics domain by construction: a paper
    integrating transcriptomics and proteomics genuinely uses transcriptomics'
    and proteomics' own vocabulary to say what it integrated. A term this
    adapter resolves therefore often also resolves under the genomics,
    transcriptomics or metabolomics adapter, because several adapters walk
    overlapping EDAM subtrees. The shared CURIE is a true label mapping in
    every case -- it is not a wrong match -- but a lone hit from this adapter is
    weak evidence, on its own, that the *multi-omics* sense rather than the
    single-layer sense was what the paper meant. Disambiguating sense is not
    ``enrich_claim``'s job; it resolves text to CURIEs and nothing more. A
    consumer running several adapters together, or a downstream reader of
    ``ontology_terms``, should weigh a match this adapter alone produced
    differently from one several domain adapters agree on.

    Every qualifier matches ``^[a-z][a-z0-9_]*$`` (snake_case), required because
    Perspicacite routes adapter qualifiers onto the open ``asb:domainQualifier``
    slot whose SHACL shape enforces that pattern. Enforced by
    ``tests/test_protocol_conformance.py``.
    """

    domain_id = "multi-omics"
    api_version = 1

    # ASB's classification layer reads ``primary_domain`` in preference to
    # ``domain_id``, and unions it into the controlled vocabulary. Declaring it
    # here is what stops a multi-omics paper classifying as "other".
    primary_domain = "multi-omics"

    qualifiers: frozenset[str] = frozenset(
        {
            # --- Layers combined -------------------------------------------------
            "integrates",  # object is an omics layer this claim combines
            "paired_with",  # object is another layer profiled on the same samples
            "matched_across",  # object is the cohort/platform unpaired layers are matched on
            # --- Integration method ------------------------------------------------
            "integrated_by",  # object is the integration method or tool
            "factorized_by",  # object is the joint factor-analysis method used
            "embedded_by",  # object is the joint embedding or dimensionality-reduction method
            "fused_by",  # object is the network-fusion method combining layer networks
            "clustered_by",  # object is the clustering method applied to the joint representation
            "weighted_by",  # object is the per-layer weight or prior used during integration
            # --- Normalisation and batch correction --------------------------------
            "normalized_by",  # object is the normalisation method applied before integration
            "batch_corrected_by",  # object is the batch-correction method or tool
            "corrected_for",  # object is the confounder removed (batch, site, platform)
            # --- Cross-layer prediction ---------------------------------------------
            "predicted_from",  # object is the source layer used to predict the subject layer
            "predicts",  # object is the target layer predicted from the subject layer
            "imputed_from",  # object is the layer used to impute values missing in the subject
            # --- Validation of the integration ---------------------------------------
            "validated_by",  # object is the orthogonal layer, assay or dataset used to validate
            "concordant_with",  # object is another layer or result the finding agrees with
            "benchmarked_against",  # object is the reference method or dataset compared against
            "evaluated_by",  # object is the metric used to assess integration quality
            # --- Cross-layer relations -------------------------------------------------
            "correlates_with",  # object is a feature or layer whose value tracks the subject
            "anti_correlates_with",  # object is a feature or layer that varies inversely
            "regulated_by",  # object is a regulatory element acting on the subject layer feature
            "associated_with",  # object is a phenotype or trait the multi-layer signature tracks
            "derived_from_cohort",  # object is the cohort or study the paired samples came from
        }
    )

    ontology_prefixes: dict[str, str] = dict(_ONTOLOGY_PREFIXES)

    # ---- classification vocabulary ------------------------------------------

    # Set by the 2026-08-25 cross-domain vocabulary audit: a term two sciences
    # both declare cannot tell them apart, so shared terms were dropped.
    subdomains: tuple[str, ...] = (
        "single-cell-multi-omics",
        "spatial-multi-omics",
        "metabologenomics",
    )

    # Same audit, same rule -- shared terms dropped as non-discriminating.
    techniques: tuple[str, ...] = (
        "multi-omics-factor-analysis",
        "similarity-network-fusion",
        "multi-block-data-analysis",
        "multi-omics-batch-effect-correction",
        "cite-seq",
        "single-cell-multiome-sequencing",
        "weighted-nearest-neighbour-integration",
    )

    # ---- protocol methods -----------------------------------------------------

    def extraction_context(self) -> str:
        """Return the domain instructions handed to the extraction model."""
        return (
            "Domain: multi-omics -- integration across two or more omics layers "
            "(joint dimensionality reduction, factor models, network fusion, "
            "cross-layer correlation, imputation of a missing layer, and the "
            "batch/normalisation problems that appear only once layers are "
            "combined). Name the layers being integrated by their own field's "
            "terminology (for example 'transcriptome', 'proteome', "
            "'metabolome') rather than a paraphrase, and name a concrete "
            "integration method or tool over a generic word: 'MOFA+' or "
            "'DIABLO' rather than 'the integration method'. State whether "
            "layers are paired on the same samples or only matched across "
            "cohorts, and which layer was predicted from which. Domain "
            "qualifiers available in addition to the base set: "
            + ", ".join(sorted(self.qualifiers))
            + "."
        )

    def enrich_claim(self, claim: dict) -> dict:
        """Attach EDAM CURIEs to the slots whose text names an EDAM concept.

        Pure: returns a new dict and never mutates the input or its nested maps.

        Matching is exact after case-folding and whitespace collapse. Substring
        and fuzzy matching over an ontology manufacture confident-looking wrong
        CURIEs ("Omics" inside "Multiomics"), and a wrong identifier is worse
        than no identifier.

        A slot that carries text but resolves to nothing is recorded under
        ``ontology_terms_unmatched`` rather than passed over, so "not an EDAM
        concept" stays distinguishable from "no attempt was made". A slot
        another adapter already resolved is left untouched.
        """
        out = dict(claim)
        terms: dict[str, str] = dict(out.get("ontology_terms") or {})
        justifications: dict[str, str] = dict(out.get("ontology_term_justifications") or {})
        unmatched: dict[str, str] = dict(out.get("ontology_terms_unmatched") or {})

        for slot in _ENRICHABLE_SLOTS:
            if slot in terms:
                continue
            value = out.get(slot)
            if not isinstance(value, str) or not value.strip():
                continue
            concept = _edam.lookup(value)
            if concept:
                terms[slot] = concept
                justifications[slot] = _LEXICAL
                unmatched.pop(slot, None)
            else:
                unmatched[slot] = value

        if terms:
            out["ontology_terms"] = terms
            out["ontology_term_justifications"] = justifications
        if unmatched:
            out["ontology_terms_unmatched"] = unmatched
        return out
