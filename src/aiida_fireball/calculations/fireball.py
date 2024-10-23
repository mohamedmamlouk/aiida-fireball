"""General `CalcJob` for Fireball calculations"""

import os

import numpy
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.folders import Folder
from aiida.engine import CalcJob
from aiida.orm import BandsData, Dict, KpointsData, RemoteData, StructureData, TrajectoryData

from .utils import _lowercase_dict, _uppercase_dict, conv_to_fortran, convert_input_to_namelist_entry


class FireballCalculation(CalcJob):
    """General `CalcJob` for Fireball calculations"""

    _PREFIX = "aiida"
    _DEFAULT_INPUT_FILE = "fireball.in"
    _DEFAULT_OUTPUT_FILE = "aiida.out"
    _DEFAULT_BAS_FILE = "aiida.bas"
    _DEFAULT_LVS_FILE = "aiida.lvs"
    _DEFAULT_KPTS_FILE = "aiida.kpts"
    _FDATA_SUBFOLDER = "./Fdata/"
    _CRASH_FILE = "CRASH"

    # Blocked keywords that are to be specified in the subclass:
    _blocked_keywords = {
        "OPTION": {
            "basisfile": _DEFAULT_BAS_FILE,
            "lvsfile": _DEFAULT_LVS_FILE,
            "kptpreference": _DEFAULT_KPTS_FILE,
            "verbosity": 3,
        }
    }

    # Additional files that should always be retrieved for the specific plugin
    _internal_retrieve_list = []

    # In restarts, will copy not symlink
    _default_symlink_usage = False

    # In restarts, it will copy the following files from the parent folder
    _restart_files_list = ["CHARGES", "*restart*"]

    # In restarts, it will copy the previous folder in the following one
    _restart_copy_to = "./"

    @classmethod
    def define(cls, spec):
        """Define inputs and outputs of the calculation."""
        super().define(spec)

        # Inputs
        spec.input("structure", valid_type=StructureData, help="The input structure.")
        spec.input("parameters", valid_type=Dict, help="The input parameters.")
        spec.input("kpoints", valid_type=KpointsData, help="The input kpoints.")
        spec.input("fdata_remote", valid_type=RemoteData, help="Remote folder containing the Fdata files.")
        spec.input("settings", valid_type=Dict, required=False, help="Additional input parameters.")
        spec.input("metadata.options.parser_name", valid_type=str, default="fireball.fireball")
        spec.input("metadata.options.input_filename", valid_type=str, default=cls._DEFAULT_INPUT_FILE)
        spec.input("metadata.options.output_filename", valid_type=str, default=cls._DEFAULT_OUTPUT_FILE)
        spec.input("metadata.options.withmpi", valid_type=bool, default=False)
        spec.input("parent_folder", valid_type=RemoteData, required=False, help="The parent remote folder to restart from.")
        spec.inputs["metadata"]["options"]["resources"].default = lambda: {
            "num_machines": 1,
            "num_cores_per_machine": 1,
        }
        spec.inputs.validator = cls.validate_inputs

        # Outputs
        spec.output(
            "output_parameters",
            valid_type=Dict,
            help="The `output_parameters` output node of the successful calculation.",
        )
        spec.output(
            "output_structure",
            valid_type=StructureData,
            required=False,
            help="The `output_structure` output node of the successful calculation if present.",
        )
        spec.output("output_trajectory", valid_type=TrajectoryData, required=False)
        spec.output(
            "output_band",
            valid_type=BandsData,
            required=False,
            help="The `output_band` output node of the successful calculation if present.",
        )
        spec.output("output_kpoints", valid_type=KpointsData, required=False)
        spec.output("output_atomic_occupations", valid_type=Dict, required=False)
        spec.default_output_node = "output_parameters"

        # Exit codes
        spec.exit_code(
            302,
            "ERROR_OUTPUT_STDOUT_MISSING",
            message="The retrieved folder did not contain the required stdout output file.",
        )
        spec.exit_code(310, "ERROR_OUTPUT_STDOUT_READ", message="The stdout output file could not be read.")
        spec.exit_code(311, "ERROR_OUTPUT_STDOUT_PARSE", message="The stdout output file could not be parsed.")
        spec.exit_code(
            312,
            "ERROR_OUTPUT_STDOUT_INCOMPLETE",
            message="The stdout output file was incomplete probably because the calculation got interrupted.",
        )
        spec.exit_code(400, "ERROR_OUT_OF_WALLTIME", message="The calculation stopped prematurely because it ran out of walltime.")
        spec.exit_code(
            340,
            "ERROR_OUT_OF_WALLTIME_INTERRUPTED",
            message="The calculation stopped prematurely because it ran out of walltime but the job was killed by the "
            "scheduler before the files were safely written to disk for a potential restart.",
        )
        spec.exit_code(350, "ERROR_UNEXPECTED_PARSER_EXCEPTION", message="The parser raised an unexpected exception: {exception}")

    @classmethod
    def validate_inputs(cls, value, _):  # pylint: disable=too-many-branches
        """Validate the entire inputs namespace."""

        # Wrapping processes may choose to exclude certain input ports in which case we can't validate. If the ports
        # have been excluded, and so are no longer part of the ``port_namespace``, skip the validation.
        # if any(key not in port_namespace for key in ("fdata_remote", "structure")):
        #     return

        # At this point, both ports are part of the namespace, and both are required so return an error message if any
        # of the two is missing.
        # for key in ("fdata_remote", "structure"):
        #     if key not in value:
        #         return f"required value was not provided for the `{key}` namespace."

        if "settings" in value:
            settings = _uppercase_dict(value["settings"].get_dict(), dict_name="settings")

            # Validate the FIXED_COORDS setting
            fixed_coords = settings.get("FIXED_COORDS", None)

            if fixed_coords is not None:
                fixed_coords = numpy.array(fixed_coords)

                if len(fixed_coords.shape) != 2 or fixed_coords.shape[1] != 3:
                    return "The `fixed_coords` setting must be a list of lists with length 3."

                if fixed_coords.dtype != bool:
                    return "All elements in the `fixed_coords` setting lists must be either `True` or `False`."

                if "structure" in value:
                    nsites = len(value["structure"].sites)

                    if len(fixed_coords) != nsites:
                        return f"Input structure has {nsites} sites, but fixed_coords has length {len(fixed_coords)}"

            dos_params = settings.get("DOS", None)

            if dos_params is not None:
                cls._blocked_keywords.setdefault("OUTPUT", {}).setdefault("iwrtdos", 1)
                valid_keys = [
                    "first_atom_index",
                    "last_atom_index",
                    "Emin",
                    "Emax",
                    "n_energy_steps",
                    "eta",
                    "iwrttip",
                    "Emin_tip",
                    "Emax_tip",
                ]
                defaults = {
                    "first_atom_index": 1,
                    "last_atom_index": len(value["structure"].sites),
                    "eta": 0.1,
                    "n_energy_steps": 100,
                    "Emin": -5.0,
                    "Emax": 5.0,
                    "iwrttip": 0,  # writes the file tip_e_str.inp
                    "Emin_tip": 0.0,
                    "Emax_tip": 0.0,
                }
                # Emin and Emax are in eV and are relative to the Fermi level:
                # conversion to Fireball format will be performed
                # There will be (n_energy_steps + 1) energy points in the output DOS file
                for key in dos_params:
                    if key not in valid_keys:
                        return f"Invalid key '{key}' in the 'DOS' namelist. Valid keys are: {valid_keys}"

                for key, default in defaults.items():
                    dos_params.setdefault(key, default)

                if dos_params["first_atom_index"] < 1 or dos_params["first_atom_index"] > len(value["structure"].sites):
                    return f"Invalid value for 'first_atom_index' in the 'DOS' namelist. \
It must be between 1 and {len(value['structure'].sites)}"
                if (
                    dos_params["last_atom_index"] < 1
                    or dos_params["last_atom_index"] > len(value["structure"].sites)
                    or dos_params["last_atom_index"] < dos_params["first_atom_index"]
                ):
                    return f"Invalid value for 'last_atom_index' in the 'DOS' namelist. \
It must be between 1 and {len(value['structure'].sites)} and greater than 'first_atom_index'"
                if dos_params["n_energy_steps"] < 1:
                    return "Invalid value for 'n_energy_steps' in the 'DOS' namelist. It must be greater than 0"
                if dos_params["eta"] <= 0.0:
                    return "Invalid value for 'eta' in the 'DOS' namelist. It must be greater than 0"
                if dos_params["iwrttip"] not in [0, 1]:
                    return "Invalid value for 'iwrttip' in the 'DOS' namelist. It must be either 0 or 1"
                if dos_params["Emin_tip"] > dos_params["Emax_tip"]:
                    return "Invalid values for 'Emin_tip' and 'Emax_tip' in the 'DOS' namelist. 'Emin_tip' must be less than 'Emax_tip'"
                if dos_params["Emin"] > dos_params["Emax"]:
                    return "Invalid values for 'Emin' and 'Emax' in the 'DOS' namelist. 'Emin' must be less than 'Emax'"

            # Update settings with the new values
            value["settings"] = Dict(settings)

    def prepare_for_submission(self, folder: Folder) -> CalcInfo:
        """Prepare the calculation job for submission by generating input files and parameters."""

        if "settings" in self.inputs:
            settings = _uppercase_dict(self.inputs.settings.get_dict(), dict_name="settings")
        else:
            settings = {}

        local_copy_list = []
        remote_copy_list = []
        remote_symlink_list = []

        # Create Fdata subfolder
        folder.get_subfolder(self._FDATA_SUBFOLDER, create=True)

        # Symlink all files in the Fdata remote folder
        remote_symlink_list.append(
            (
                self.inputs.fdata_remote.computer.uuid,
                os.path.join(self.inputs.fdata_remote.get_remote_path(), "*"),
                self._FDATA_SUBFOLDER,
            )
        )

        # Write the input file
        input_filecontent = self.generate_input(self.inputs.parameters.get_dict())

        with folder.open(self.metadata.options.input_filename, "w") as handle:
            handle.write(input_filecontent)

        # Write the bas file
        bas_filecontent = self.generate_bas(self.inputs.structure)

        with folder.open(self._DEFAULT_BAS_FILE, "w") as handle:
            handle.write(bas_filecontent)

        # Write the lvs file
        lvs_filecontent = self.generate_lvs(self.inputs.structure)

        with folder.open(self._DEFAULT_LVS_FILE, "w") as handle:
            handle.write(lvs_filecontent)

        # Write the kpts file
        kpts_filecontent = self.generate_kpts(self.inputs.kpoints, self.inputs.structure)

        with folder.open(self._DEFAULT_KPTS_FILE, "w") as handle:
            handle.write(kpts_filecontent)

        # Write the constraints file if the setting is provided
        if "FIXED_COORDS" in settings:
            fixed_coords = settings.pop("FIXED_COORDS", None)
            if fixed_coords is not None:
                fixed_coords = numpy.array(fixed_coords)
                constraints_filecontent = self.generate_constraints(self.inputs.structure, fixed_coords)

                with folder.open("FRAGMENTS", "w") as handle:
                    handle.write(constraints_filecontent)

        # Write the dos.optional file if the setting is provided
        if "DOS" in settings:
            dos_params = settings.pop("DOS", None)
            if dos_params is not None:
                parent_output_parameters = self.inputs.parent_folder.creator.outputs.output_parameters.get_dict()
                dos_optional_filecontent = self.generate_dos_optional(dos_params, parent_output_parameters.get("fermi_energy", 0.0))

                with folder.open("dos.optional", "w") as handle:
                    handle.write(dos_optional_filecontent)

        # operations for restart
        symlink = settings.pop("PARENT_FOLDER_SYMLINK", self._default_symlink_usage)  # a boolean
        if symlink:
            if "parent_folder" in self.inputs:
                for file_name in self._restart_files_list:
                    remote_symlink_list.append(
                        (
                            self.inputs.parent_folder.computer.uuid,
                            os.path.join(self.inputs.parent_folder.get_remote_path(), file_name),
                            self._restart_copy_to,
                        )
                    )
        elif "parent_folder" in self.inputs:
            for file_name in self._restart_files_list:
                remote_copy_list.append(
                    (
                        self.inputs.parent_folder.computer.uuid,
                        os.path.join(self.inputs.parent_folder.get_remote_path(), file_name),
                        self._restart_copy_to,
                    )
                )

        # Prepare the code info
        codeinfo = CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.cmdline_params = []  # Fireball reads directly from the input file 'fireball.in'
        codeinfo.stdout_name = self.inputs.metadata.options.output_filename

        # Prepare the calculation info
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.codes_info = [codeinfo]

        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list
        calcinfo.remote_symlink_list = remote_symlink_list

        # Retrieve by default the output file and any additional files specified in the settings
        calcinfo.retrieve_list = []
        calcinfo.retrieve_list.append(self.metadata.options.output_filename)
        calcinfo.retrieve_list.append(self._CRASH_FILE)
        calcinfo.retrieve_list += settings.pop("ADDITIONAL_RETRIEVE_LIST", [])
        calcinfo.retrieve_list += self._internal_retrieve_list

        return calcinfo

    @classmethod
    def generate_input(cls, parameters):
        """Generate the input data for the calculation."""
        file_lines = []

        input_params = _uppercase_dict(parameters, dict_name="parameters")
        input_params = {k: _lowercase_dict(v, dict_name=k) for k, v in input_params.items()}

        blocked_keywords = _uppercase_dict(cls._blocked_keywords, dict_name="blocked_keywords")
        blocked_keywords = {k: _lowercase_dict(v, dict_name=k) for k, v in blocked_keywords.items()}

        # Check if there are blocked keywords in the input parameters
        for namelist_name, namelist in blocked_keywords.items():
            for key, value in namelist.items():
                if key in input_params.get(namelist_name, {}):
                    raise ValueError(f"Cannot specify the '{key}' keyword in the '{namelist_name}' namelist.")

        # Add keywords from the blocked keywords which have values that are not None to the input parameters
        for namelist_name, namelist in blocked_keywords.items():
            for key, value in namelist.items():
                if value is not None:
                    if namelist_name not in input_params:
                        input_params[namelist_name] = {}
                    input_params[namelist_name][key] = value

        # Write the namelists
        for namelist_name, namelist in sorted(input_params.items()):
            file_lines.append(f"&{namelist_name}")
            for key, value in sorted(namelist.items()):
                file_lines.append(convert_input_to_namelist_entry(key, value)[:-1])
            file_lines.append("&END")

        return "\n".join(file_lines) + "\n"

    @classmethod
    def generate_bas(cls, structure: StructureData):
        """Generate the bas file for the calculation (atomic positions)."""
        ase_structure = structure.get_ase()
        file_lines = []
        file_lines.append(f"\t{len(ase_structure):3d}")

        for atom in ase_structure:
            file_lines.append(
                f"{atom.number:3d} \
{conv_to_fortran(atom.position[0])} \
{conv_to_fortran(atom.position[1])} \
{conv_to_fortran(atom.position[2])}"
            )

        return "\n".join(file_lines) + "\n"

    @classmethod
    def generate_lvs(cls, structure: StructureData):
        """Generate the lvs file for the calculation (lattice vectors)."""
        ase_structure = structure.get_ase()
        file_lines = []
        for vector in ase_structure.cell:
            file_lines.append(f"{conv_to_fortran(vector[0])} {conv_to_fortran(vector[1])} {conv_to_fortran(vector[2])}")

        return "\n".join(file_lines) + "\n"

    @classmethod
    def generate_kpts(cls, kpoints: KpointsData, structure: StructureData):
        """Generate the kpts file for the calculation (write list of cartesian k-points)."""
        file_lines = []
        temp_kpoints = KpointsData()
        temp_kpoints.set_cell_from_structure(structure)
        if "kpoints" in kpoints.get_arraynames():
            scaled_kpoints = kpoints.get_kpoints()
        else:
            scaled_kpoints = kpoints.get_kpoints_mesh(print_list=True)
        temp_kpoints.set_kpoints(scaled_kpoints, cartesian=False, weights=[1.0 / len(scaled_kpoints)] * len(scaled_kpoints))
        cartesian_kpoints, weights = temp_kpoints.get_kpoints(cartesian=True, also_weights=True)
        file_lines.append(f"\t{len(cartesian_kpoints):5d}")
        for kpt, weight in zip(cartesian_kpoints, weights):
            file_lines.append(f"{conv_to_fortran(kpt[0])} {conv_to_fortran(kpt[1])} {conv_to_fortran(kpt[2])}\t{weight:.10f}")

        return "\n".join(file_lines) + "\n"

    def generate_constraints(self, structure: StructureData, fixed_coords: numpy.ndarray):
        """Generate the constraints file for the calculation."""
        ase_structure = structure.get_ase()
        file_lines = []
        file_lines.append("0")
        file_lines.append("1")
        file_lines.append(f"{len(ase_structure):3d}")

        for i, fix in zip(range(len(ase_structure)), fixed_coords):
            file_lines.append(f"{i+1:3d} {int(fix[0]):1d} {int(fix[1]):1d} {int(fix[2]):1d}")

        return "\n".join(file_lines) + "\n"

    def generate_dos_optional(self, dos_params: dict, fermi_energy: float) -> str:
        """Generate the content of the file dos.optional"""
        file_lines = []
        file_lines.append("1.0")
        file_lines.append(f"{dos_params['first_atom_index']:3d}\t{dos_params['last_atom_index']:3d}\t! First and last atom index")
        file_lines.append(f"{dos_params['n_energy_steps']}\t! Number of energy steps")
        file_lines.append(
            f"{dos_params['Emin'] + fermi_energy:.6f}\t{(dos_params['Emax'] - dos_params['Emin'])/dos_params['n_energy_steps']}\t! Emin and dE"
        )
        file_lines.append(f"{dos_params['iwrttip']:1d}\t! iwrttip=1 writes the file tip_e_str.inp")
        file_lines.append(f"{dos_params['Emin_tip']:6f}\t{dos_params['Emax_tip']:6f}\t! Emin_tip and Emax_tip")
        file_lines.append(f"{dos_params['eta']:.6f}\t! eta")

        return "\n".join(file_lines) + "\n"
