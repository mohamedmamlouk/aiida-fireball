# -*- coding: utf-8 -*-
"""Tests for the `FireballCalculation` class."""

import os

import numpy as np
import pytest
from aiida import orm
from aiida.common import datastructures

# from aiida.common.exceptions import InputValidationError
from aiida.plugins import CalculationFactory
from aiida_fireball.calculations.fireball import FireballCalculation


def test_calculation():
    """Test the `FireballCalculation` load."""
    calc = CalculationFactory("fireball.fireball")
    assert issubclass(calc, FireballCalculation)


@pytest.mark.parametrize(
    ["symlink_restart", "mesh"],
    [
        (False, False),
        (True, False),
        (False, True),
    ],
)
def test_fireball_default(
    fixture_sandbox,
    generate_calc_job,
    generate_inputs_fireball,
    file_regression,
    symlink_restart: bool,
    generate_kpoints_mesh,
    generate_kpoints,
    mesh: bool,
):
    """Test a default `FireballCalculation`."""
    entry_point_name = "fireball.fireball"

    inputs = generate_inputs_fireball()
    if symlink_restart:
        inputs["settings"] = orm.Dict(dict={"PARENT_FOLDER_SYMLINK": symlink_restart})
    if mesh:
        inputs["kpoints"] = generate_kpoints_mesh(3)
    else:
        inputs["kpoints"] = generate_kpoints(kpts=np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.5]]))
    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)

    cmdline_params = ["aiida.in"]
    remote_symlink_list = [(inputs["fdata_remote"].computer.uuid, inputs["fdata_remote"].get_remote_path(), "./Fdata/")]

    if symlink_restart:
        remote_symlink_list.append(
            (
                inputs["parent_folder"].computer.uuid,
                os.path.join(inputs["parent_folder"].get_remote_path(), "./out/*"),
                "./out/",
            )
        )

    # Check the attributes of the returned `CalcInfo`
    assert isinstance(calc_info, datastructures.CalcInfo)
    assert isinstance(calc_info.codes_info[0], datastructures.CodeInfo)
    assert sorted(calc_info.codes_info[0].cmdline_params) == cmdline_params
    assert sorted(calc_info.remote_symlink_list) == sorted(remote_symlink_list)

    with fixture_sandbox.open("aiida.in") as handle:
        input_written = handle.read()

    # Checks on the files written to the sandbox folder as raw input
    assert sorted(fixture_sandbox.get_content_list()) == sorted(
        ["out", "aiida.in", "aiida.bas", "aiida.lvs", "aiida.kpts"]
    )
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


def test_fireball_fixed_coords(fixture_sandbox, generate_calc_job, generate_inputs_fireball, file_regression):
    """Test a `FireballCalculation` where the `fixed_coords` setting was provided."""
    entry_point_name = "fireball.fireball"

    inputs = generate_inputs_fireball()
    inputs["settings"] = orm.Dict(dict={"FIXED_COORDS": [[True, True, False], [False, True, False]]})
    generate_calc_job(fixture_sandbox, entry_point_name, inputs)

    with fixture_sandbox.open("aiida.in") as handle:
        input_written = handle.read()

    file_regression.check(input_written, encoding="utf-8", extension=".in")


@pytest.mark.parametrize(
    ["fixed_coords", "error_message"],
    [
        ([[True, True], [False, True]], "The `fixed_coords` setting must be a list of lists with length 3."),
        (
            [[True, True, 1], [False, True, False]],
            "All elements in the `fixed_coords` setting lists must be either `True` or `False`.",
        ),
        ([[True, True, False]], "Input structure has 2 sites, but fixed_coords has length 1"),
    ],
)
def test_fireball_fixed_coords_validation(
    fixture_sandbox, generate_calc_job, generate_inputs_fireball, fixed_coords, error_message
):
    """Test the validation for the `fixed_coords` setting."""
    entry_point_name = "fireball.fireball"

    inputs = generate_inputs_fireball()
    inputs["settings"] = orm.Dict(dict={"FIXED_COORDS": fixed_coords})

    with pytest.raises(ValueError, match=error_message):
        generate_calc_job(fixture_sandbox, entry_point_name, inputs)


def test_fireball_missing_inputs(fixture_sandbox, generate_calc_job, generate_inputs_fireball):
    """Test a `FireballCalculation` with missing required inputs."""
    entry_point_name = "fireball.fireball"

    inputs = generate_inputs_fireball()
    del inputs["fdata_remote"]
    error_message = "Error occurred validating port 'inputs.fdata_remote': "
    error_message += "required value was not provided for 'fdata_remote'"

    with pytest.raises(
        ValueError,
        match=error_message,
    ):
        generate_calc_job(fixture_sandbox, entry_point_name, inputs)
