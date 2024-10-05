# test_utils.py
import pytest
from aiida.common import exceptions
from aiida_fireball.calculations.utils import (
    _case_transform_dict,
    _lowercase_dict,
    _uppercase_dict,
    conv_to_fortran,
    convert_input_to_namelist_entry,
)


def test_lowercase_dict():
    input_dict = {"KeyOne": 1, "KeyTwo": 2}
    expected_output = {"keyone": 1, "keytwo": 2}
    assert _lowercase_dict(input_dict, "test_dict") == expected_output


def test_uppercase_dict():
    input_dict = {"keyone": 1, "keytwo": 2}
    expected_output = {"KEYONE": 1, "KEYTWO": 2}
    assert _uppercase_dict(input_dict, "test_dict") == expected_output


def test_case_transform_dict_type_error():
    with pytest.raises(TypeError):
        _case_transform_dict("not_a_dict", "test_dict", "_case_transform_dict", str.lower)


def test_case_transform_dict_input_validation_error():
    input_dict = {"KeyOne": 1, "keyone": 2}
    with pytest.raises(exceptions.InputValidationError):
        _case_transform_dict(input_dict, "test_dict", "_case_transform_dict", str.lower)


def test_conv_to_fortran_bool():
    assert conv_to_fortran(True) == ".true."
    assert conv_to_fortran(False) == ".false."


def test_conv_to_fortran_int():
    assert conv_to_fortran(42) == "42"


def test_conv_to_fortran_float():
    assert conv_to_fortran(3.14159) == "  3.1415900000d+00"


def test_conv_to_fortran_str():
    assert conv_to_fortran("test") == "'test'"
    assert conv_to_fortran("test", quote_strings=False) == "test"


def test_conv_to_fortran_invalid_type():
    with pytest.raises(ValueError):
        conv_to_fortran([1, 2, 3])


def test_convert_input_to_namelist_entry_single_value():
    assert convert_input_to_namelist_entry("key", 42) == "  key = 42\n"


def test_convert_input_to_namelist_entry_list():
    assert convert_input_to_namelist_entry("key", [1, 2, 3]) == "  key(1) = 1\n  key(2) = 2\n  key(3) = 3\n"


def test_convert_input_to_namelist_entry_double_nested_list():
    val = [[1, 1, 3, 3.5], [2, 1, 1, 2.8]]
    expected_output = f"  key(1,1,3) = {conv_to_fortran(3.5)}\n  key(2,1,1) = {conv_to_fortran(2.8)}\n"
    assert convert_input_to_namelist_entry("key", val) == expected_output


def test_convert_input_to_namelist_entry_double_nested_list_with_mapping():
    val = [[2, "Ni", 3.5], [2, "Fe", 7.4]]
    mapping = {"Ni": 1, "Fe": 3}
    expected_output = f"  key(2,1) = {conv_to_fortran(3.5)}\n  key(2,3) = {conv_to_fortran(7.4)}\n"
    assert convert_input_to_namelist_entry("key", val, mapping) == expected_output


def test_convert_input_to_namelist_entry_dict():
    val = {"Co": 3.5, "O": 7.4}
    mapping = {"Co": 1, "O": 3}
    expected_output = f"  key(1) = {conv_to_fortran(3.5)}\n  key(3) = {conv_to_fortran(7.4)}\n"
    assert convert_input_to_namelist_entry("key", val, mapping) == expected_output


def test_convert_input_to_namelist_entry_dict_no_mapping():
    val = {"Co": 3.5, "O": 7.4}
    with pytest.raises(ValueError):
        convert_input_to_namelist_entry("key", val)


def test_convert_input_to_namelist_entry_double_nested_list_invalid_value():
    val = [[1, 1, 3, 3.5], [2, 1, "invalid", 2.8]]
    with pytest.raises(ValueError):
        convert_input_to_namelist_entry("key", val)


def test_convert_input_to_namelist_entry_double_nested_list_no_mapping():
    val = [[2, "Ni", 3.5], [2, "Unknown", 7.4]]
    mapping = {"Ni": 1}
    with pytest.raises(ValueError):
        convert_input_to_namelist_entry("key", val, mapping)
