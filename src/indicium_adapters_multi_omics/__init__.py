"""Multi-omics DomainAdapter for the indicium ecosystem.

Exposes :class:`MultiOmicsAdapter` via the ``indicium.adapters`` entry point, so
``indicium_adapters.discover_adapters()`` finds it on install and ASB's
classification vocabulary picks up ``primary_domain="multi-omics"``.
"""

from .multi_omics import MultiOmicsAdapter

__all__ = ["MultiOmicsAdapter", "__version__"]

__version__ = "0.1.0"
