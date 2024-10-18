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
    match = re.search(r"Fermi Level =\s*([+-]?\d+\.\d+)", stdout)
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
        parsed_data["energy_tolerance_units"] = "eV"

    # Parse force tolerance
    match = re.search(r"force tolerance =\s*(\d+\.\d+(E[+-]\d+)?)\s*\[eV/A\]", stdout)
    if match:
        parsed_data["force_tolerance"] = float(match.group(1))
        parsed_data["force_tolerance_units"] = "eV/A"

    # Parse sigma tolerance
    match = re.search(r"sigmatol =\s*(\d+\.\d+(E[+-]\d+)?)", stdout)
    if match:
        parsed_data["sigma_tolerance"] = float(match.group(1))

    # Parse beta mixing
    match = re.search(r"bmix =\s*(\d+\.\d+(E[+-]\d+)?)", stdout)
    if match:
        parsed_data["beta_mixing"] = float(match.group(1))

    # Parse the charge state
    match = re.search(r"qstate =\s*(\d+\.\d+(E[+-]\d+)?)", stdout)
    if match:
        parsed_data["charge_state"] = float(match.group(1))

    # Parse charge type
    match = re.search(r"iqout =\s*(\d)", stdout)
    if match:
        charge_types = {1: "Lowdin", 2: "Mulliken", 3: "Natural"}
        parsed_data["charge_type"] = charge_types[int(match.group(1))]

    return parsed_data
