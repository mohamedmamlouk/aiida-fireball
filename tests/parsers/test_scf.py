"""Tests for the `ScfParser`."""

import pytest
from aiida_fireball.calculations.scf import ScfCalculation
from aiida_fireball.parsers.scf import ScfParser


@pytest.fixture(autouse=True)
def add_scf_entry_points(entry_points):
    """Add the `ScfCalculation` and `ScfParser` entry points in function scope."""
    entry_points.add(ScfCalculation, "aiida.calculations:fireball.scf")
    entry_points.add(ScfParser, "aiida.parsers:fireball.scf")
