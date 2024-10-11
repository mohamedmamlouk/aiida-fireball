"""Base `CalcJob` for Fireball calculations"""

import os

import numpy
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.folders import Folder
from aiida.engine import CalcJob
from aiida.orm import Dict, KpointsData, RemoteData, StructureData

from .utils import _lowercase_dict, _uppercase_dict, conv_to_fortran, convert_input_to_namelist_entry


class BaseFireballCalculation(CalcJob):
    """Base `CalcJob` for Fireball calculations"""

    _PREFIX = "aiida"
    _DEFAULT_INPUT_FILE = "aiida.in"
    _DEFAULT_OUTPUT_FILE = "aiida.out"
    _DEFAULT_BAS_FILE = "aiida.bas"
    _DEFAULT_LVS_FILE = "aiida.lvs"
    _DEFAULT_KPTS_FILE = "aiida.kpts"
    _FDATA_SUBFOLDER = "./Fdata/"
    _CRASH_FILE = "CRASH"

    # Name lists to print by calculation type
    _automatic_namelists = {}

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

        spec.input("structure", valid_type=StructureData, help="The input structure.")
        spec.input("parameters", valid_type=Dict, help="The input parameters.")
        spec.input("kpoints", valid_type=KpointsData, help="The input kpoints.")
        spec.input("fdata_remote", valid_type=RemoteData, help="Remote folder containing the Fdata files.")
        spec.input("settings", valid_type=Dict, required=False, help="Additional input parameters.")
        spec.input("metadata.options.input_filename", valid_type=str, default=cls._DEFAULT_INPUT_FILE)
        spec.input("metadata.options.output_filename", valid_type=str, default=cls._DEFAULT_OUTPUT_FILE)
        spec.input("metadata.options.withmpi", valid_type=bool, default=True)
        spec.input(
            "parent_folder", valid_type=RemoteData, required=False, help="The parent remote folder to restart from."
        )
        spec.inputs["metadata"]["options"]["resources"].default = lambda: {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        }
        spec.inputs.validator = cls.validate_inputs

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
        spec.exit_code(
            400, "ERROR_OUT_OF_WALLTIME", message="The calculation stopped prematurely because it ran out of walltime."
        )

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
        codeinfo.cmdline_params = [self.inputs.metadata.options.input_filename]
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
        temp_kpoints.set_kpoints(
            scaled_kpoints, cartesian=False, weights=[1.0 / len(scaled_kpoints)] * len(scaled_kpoints)
        )
        cartesian_kpoints, weights = temp_kpoints.get_kpoints(cartesian=True, also_weights=True)
        file_lines.append(f"\t{len(cartesian_kpoints):5d}")
        for kpt, weight in zip(cartesian_kpoints, weights):
            file_lines.append(
                f"{conv_to_fortran(kpt[0])} {conv_to_fortran(kpt[1])} {conv_to_fortran(kpt[2])}\t{weight:.10f}"
            )

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
