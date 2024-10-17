"""Tests for the `ScfCalculation` class."""

import os

import pytest
from aiida.common import datastructures
from aiida.plugins import CalculationFactory
from aiida_fireball.calculations.scf import ScfCalculation


@pytest.fixture(autouse=True)
def add_scf_entry_point(entry_points):
    """Add the `ScfCalculation` entry point in function scope."""
    entry_points.add(ScfCalculation, "aiida.calculations:fireball.scf")


def test_calculation():
    """Test the `ScfCalculation` load."""
    calc = CalculationFactory("fireball.scf")
    assert issubclass(calc, ScfCalculation)


def test_fireball_default(
    fixture_sandbox,
    generate_calc_job,
    generate_inputs_scf_fireball,
    file_regression,
):
    """Test a default `ScfCalculation`."""
    entry_point_name = "fireball.scf"

    inputs = generate_inputs_scf_fireball()
    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)

    cmdline_params = ["aiida.in"]
    remote_symlink_list = [
        (inputs["fdata_remote"].computer.uuid, os.path.join(inputs["fdata_remote"].get_remote_path(), "*"), "./Fdata/")
    ]

    # Check the attributes of the returned `CalcInfo`
    assert isinstance(calc_info, datastructures.CalcInfo)
    assert isinstance(calc_info.codes_info[0], datastructures.CodeInfo)
    assert sorted(calc_info.codes_info[0].cmdline_params) == cmdline_params
    assert sorted(calc_info.remote_symlink_list) == sorted(remote_symlink_list)

    # Checks on the files written to the sandbox folder as raw input
    assert sorted(fixture_sandbox.get_content_list()) == sorted(
        ["Fdata", "aiida.in", "aiida.bas", "aiida.lvs", "aiida.kpts"]
    )

    # Check the content of the in file
    with fixture_sandbox.open("aiida.in") as handle:
        input_written = handle.read()
    file_regression.check(input_written, encoding="utf-8", extension=".in")

    # Check the content of the bas file
    with fixture_sandbox.open("aiida.bas") as handle:
        bas_written = handle.read()
    file_regression.check(bas_written, encoding="utf-8", extension=".bas")

    # Check the content of the lvs file
    with fixture_sandbox.open("aiida.lvs") as handle:
        lvs_written = handle.read()
    file_regression.check(lvs_written, encoding="utf-8", extension=".lvs")

    # Check the content of the kpts file
    with fixture_sandbox.open("aiida.kpts") as handle:
        kpts_written = handle.read()
    file_regression.check(kpts_written, encoding="utf-8", extension=".kpts")
