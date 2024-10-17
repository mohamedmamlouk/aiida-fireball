"""Raw parsers for Fireball output files."""

import re


def parse_raw_stdout(stdout):
    """Parse the raw stdout output of a Fireball calculation.

    :param stdout: the stdout content as a string
    :return: the parsed data
    """
    parsed_data = {}

    # Parse the walltime
    match = re.search(r"FIREBALL RUNTIME :\s*(\d+\.\d+)\s*\[sec\]", stdout)
    if match:
        parsed_data["wall_time_seconds"] = float(match.group(1))

    # Parse the total energy
    match = re.search(r"ETOT =\s*([+-]?\d+\.\d+)", stdout)
    if match:
        parsed_data["total_energy"] = float(match.group(1))
        parsed_data["total_energy_units"] = "eV"

    # Parse the Fermi energy
    match = re.search(r"Fermi level =\s*([+-]?\d+\.\d+)", stdout)
    if match:
        parsed_data["fermi_energy"] = float(match.group(1))
        parsed_data["fermi_energy_units"] = "eV"

    # Parse the number of electrons
    match = re.search(r"qztot =\s*(\d+\.\d+)", stdout)
    if match:
        parsed_data["number_of_electrons"] = float(match.group(1))

    # Parse energy tolerance
    match = re.search(r"energy tolerance =\s*(\d+\.\d+(E[+-]\d+)?)\s*\[eV\]", stdout)
    if match:
        parsed_data["energy_tolerance"] = float(match.group(1))

    return parsed_data
