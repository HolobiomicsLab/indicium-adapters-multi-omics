"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from indicium_adapters_multi_omics import MultiOmicsAdapter


@pytest.fixture
def adapter() -> MultiOmicsAdapter:
    return MultiOmicsAdapter()
