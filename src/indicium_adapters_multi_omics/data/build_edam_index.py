"""Maintainer script: regenerate ``edam_index.json`` from EDAM via EBI OLS4.

The index is the label spine ``_edam.py`` matches claim text against, and the
same walk emits the ``subtopics`` and ``techniques`` lists that become
``MultiOmicsAdapter.subdomains`` and ``MultiOmicsAdapter.techniques``. It is cut
from a recorded set of EDAM roots: each root contributes itself and its direct
subclasses, and each of those contributes its preferred label plus every exact
synonym EDAM records. Nothing is hand-added -- a label that EDAM does not carry
resolves to a CURIE EDAM never issued, which is the wrong-CURIE failure the
whole package is built to avoid.

Usage (never run at install or import time)::

    python -m indicium_adapters_multi_omics.data.build_edam_index

Re-run on an EDAM release.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Final

OLS_TERMS_URL: Final[str] = "https://www.ebi.ac.uk/ols4/api/ontologies/edam/terms"

EDAM_IRI_PREFIX: Final[str] = "http://edamontology.org/"

EDAM_CURIE_PREFIX: Final[str] = "edam"

# Multiomics. It names the domain itself, so -- as with every sibling adapter --
# it is excluded from its own vocabulary rather than listed as a peer of the
# things it classifies.
DOMAIN_ROOT: Final[str] = f"{EDAM_IRI_PREFIX}topic_4021"

# Omics: the parent EDAM files every single-omics topic under. A multi-omics
# paper integrates "layers" and names each layer with this vocabulary --
# Genomics, Proteomics, Metabolomics, and so on -- rather than with a word of
# its own. This is the vocabulary decision the brief makes; nothing else is
# added to it.
LAYER_ROOTS: Final[tuple[str, ...]] = (f"{EDAM_IRI_PREFIX}topic_3391",)

# Multiomics itself has no EDAM subclasses (it is a leaf), and Omics files the
# layers being combined, not the methods that combine them -- so neither root
# reaches a technique vocabulary. The three operations below are EDAM's own
# filing for the methods this field is defined by: joint dimensionality
# reduction / factor models, network fusion, and missing-layer imputation (see
# the brief's field notes). Each is added as a root for exactly the reason
# Metatranscriptomics was added to the genomics generator: EDAM carries the
# concept, but files it somewhere the domain root's own subtree does not reach.
# "Clustering" (operation_3432) and "Data integration and warehousing"
# (topic_3366) were considered and rejected: the former's children include
# domains as unrelated as document clustering, and the latter is a leaf with
# nothing under it to collect.
TECHNIQUE_ROOTS: Final[tuple[str, ...]] = (
    f"{EDAM_IRI_PREFIX}operation_3935",  # Dimensionality reduction
    f"{EDAM_IRI_PREFIX}operation_3927",  # Network analysis
    f"{EDAM_IRI_PREFIX}operation_3557",  # Imputation
)

ROOTS: Final[tuple[str, ...]] = (DOMAIN_ROOT, *LAYER_ROOTS, *TECHNIQUE_ROOTS)

SOURCE: Final[str] = "EDAM (edamontology.org/EDAM.csv); entries verified against EBI OLS4"

CHILD_PAGE_SIZE: Final[int] = 200

REQUEST_TIMEOUT_SECONDS: Final[int] = 60


def _normalise(text: str) -> str:
    """Case-fold and collapse whitespace, matching ``_edam.lookup``'s key form."""
    return " ".join(str(text).lower().split())


def _fetch(url: str) -> dict:
    """GET ``url`` and return the decoded JSON body."""
    with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.load(response)


def _term(iri: str) -> dict:
    """Return the OLS4 term record for one EDAM ``iri``."""
    query = urllib.parse.urlencode({"iri": iri})
    terms = _fetch(f"{OLS_TERMS_URL}?{query}").get("_embedded", {}).get("terms", [])
    if not terms:
        raise RuntimeError(f"EDAM has no term {iri}")
    return terms[0]


def _children(term: dict) -> list[dict]:
    """Return the direct subclasses of ``term``, or [] when it is a leaf."""
    link = term["_links"].get("hierarchicalChildren", {}).get("href")
    if not link:
        return []
    page = _fetch(f"{link}?size={CHILD_PAGE_SIZE}")
    return page.get("_embedded", {}).get("terms", [])


def _entries(term: dict) -> dict[str, str]:
    """Map every label and exact synonym of ``term`` to its ``edam:`` CURIE."""
    local = term["iri"].removeprefix(EDAM_IRI_PREFIX)
    curie = f"{EDAM_CURIE_PREFIX}:{local}"
    names = [term["label"], *(term.get("synonyms") or [])]
    return {_normalise(name): curie for name in names if str(name).strip()}


def _slug(label: str) -> str:
    """Return ``label`` as the kebab-case slug the classification vocabulary uses."""
    return "-".join(_normalise(label).split())


def _collect(roots: tuple[str, ...]) -> dict[str, dict]:
    """Return every EDAM term reachable from ``roots``, keyed by IRI.

    Each root contributes itself and its direct subclasses only -- the same
    one-level walk every sibling adapter uses, so a technique root does not
    quietly pull in a second layer of unrelated vocabulary.
    """
    terms: dict[str, dict] = {}
    for iri in roots:
        root = _term(iri)
        for term in (root, *_children(root)):
            terms.setdefault(term["iri"], term)
    return terms


def _index_of(terms: list[dict]) -> dict[str, str]:
    """Map every label and exact synonym across ``terms`` to its ``edam:`` CURIE."""
    index: dict[str, str] = {}
    for term in terms:
        index.update(_entries(term))
    return dict(sorted(index.items()))


def _slugs_of(terms: dict[str, dict], *, excluding: tuple[str, ...] = ()) -> list[str]:
    """Return the sorted, deduplicated label slugs of ``terms``, dropping ``excluding``."""
    return sorted({_slug(term["label"]) for iri, term in terms.items() if iri not in excluding})


def main() -> None:
    """Rebuild ``edam_index.json`` next to this script from the recorded roots.

    Subdomains and techniques are collected separately, from disjoint root
    groups, so the two vocabularies cannot bleed into each other; the concept
    index itself is the union of everything collected, because ``enrich_claim``
    resolves claim text against the whole vocabulary regardless of which
    property a term also feeds.
    """
    domain_terms = _collect((DOMAIN_ROOT,))
    layer_terms = _collect(LAYER_ROOTS)
    technique_terms = _collect(TECHNIQUE_ROOTS)
    all_terms = {**domain_terms, **layer_terms, **technique_terms}

    payload = {
        "index": _index_of(list(all_terms.values())),
        # ``layer_terms`` (Omics + its direct children) contains two entries that
        # are not themselves an omics layer a paper integrates: Omics, the root
        # (LAYER_ROOTS[0]), and Multiomics (DOMAIN_ROOT), which is structurally
        # filed as one of Omics's own children in EDAM. Both must be dropped, or
        # "omics" / "multiomics" leak into subtopics as a false layer.
        "subtopics": _slugs_of(layer_terms, excluding=(*LAYER_ROOTS, DOMAIN_ROOT)),
        "techniques": _slugs_of(technique_terms),
        "roots": list(ROOTS),
        "source": SOURCE,
    }
    target = Path(__file__).parent / "edam_index.json"
    target.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
    print(f"[edam] wrote {target} with {len(payload['index']):,} entries", file=sys.stderr)


if __name__ == "__main__":
    main()
