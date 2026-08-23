"""Contract for ``MultiOmicsAdapter.enrich_claim``.

Enrichment runs over claim dicts that are already extracted and validated;
nothing here reads article text.
"""

from __future__ import annotations


def test_resolves_a_layer_name_with_a_lexical_justification(adapter):
    out = adapter.enrich_claim({"subject": "Genomics", "qualifier": "integrated_by"})
    assert out["ontology_terms"]["subject"] == "edam:topic_0622"
    assert out["ontology_term_justifications"]["subject"] == "semapv:LexicalMatching"


def test_resolves_a_technique_name(adapter):
    out = adapter.enrich_claim({"object": "Network analysis"})
    assert out["ontology_terms"]["object"] == "edam:operation_3927"


def test_resolves_the_domain_root_itself(adapter):
    out = adapter.enrich_claim({"subject": "Multiomics"})
    assert out["ontology_terms"]["subject"] == "edam:topic_4021"


def test_lookup_is_case_and_whitespace_insensitive(adapter):
    spaced = adapter.enrich_claim({"subject": "  mUlTi-Omics  "})
    exact = adapter.enrich_claim({"subject": "Multi-omics"})
    assert spaced["ontology_terms"]["subject"] == exact["ontology_terms"]["subject"]


def test_records_slots_it_could_not_resolve_instead_of_staying_silent(adapter):
    claim = {"subject": "our bespoke integration pipeline v3", "object": "Imputation"}
    out = adapter.enrich_claim(claim)
    assert out["ontology_terms"]["object"] == "edam:operation_3557"
    assert out["ontology_terms_unmatched"]["subject"] == "our bespoke integration pipeline v3"
    assert "subject" not in out["ontology_terms"]


def test_substring_of_a_concept_does_not_resolve(adapter):
    """A prefix of a real index entry must not pick that entry up -- a wrong
    CURIE is worse than no CURIE. Both strings below are proper substrings of
    concepts the shipped index does carry."""
    for prefix in ("multi-omic", "genomic"):
        assert adapter.enrich_claim({"subject": prefix}).get("ontology_terms") is None


def test_does_not_overwrite_a_term_another_adapter_already_set(adapter):
    claim = {"subject": "Genomics", "ontology_terms": {"subject": "CHEBI:99999"}}
    out = adapter.enrich_claim(claim)
    assert out["ontology_terms"]["subject"] == "CHEBI:99999"


def test_enrich_claim_does_not_mutate_nested_maps(adapter):
    """Regression: copying only the outer dict leaks writes back into the caller."""
    terms: dict[str, str] = {}
    claim = {"subject": "Genomics", "ontology_terms": terms}
    adapter.enrich_claim(claim)
    assert terms == {}


def test_non_string_and_empty_slots_are_skipped_not_crashed(adapter):
    out = adapter.enrich_claim({"subject": None, "object": "", "qualifier": 42})
    assert not out.get("ontology_terms")
    assert not out.get("ontology_terms_unmatched")


def test_a_term_shared_with_a_single_omics_domain_still_resolves_honestly(adapter):
    """"Genomics" and "Proteomics" are true EDAM label mappings here as much as
    they are for the genomics/proteomics adapters -- the adapter does not
    refuse a term merely because another domain also claims it (see the class
    docstring on why this is weak, not wrong, evidence of domain intent)."""
    out = adapter.enrich_claim({"subject": "Genomics", "object": "Proteomics"})
    assert out["ontology_terms"]["subject"] == "edam:topic_0622"
    assert out["ontology_terms"]["object"] == "edam:topic_0121"


def test_unrelated_keys_are_preserved(adapter):
    out = adapter.enrich_claim({"subject": "Metabolomics", "claim_id": "c1", "confidence": 0.9})
    assert out["claim_id"] == "c1"
    assert out["confidence"] == 0.9


def test_a_qualifier_carrying_a_technique_name_still_resolves(adapter):
    out = adapter.enrich_claim({"subject": "the joint model", "qualifier": "Imputation"})
    assert out["ontology_terms"]["qualifier"] == "edam:operation_3557"
