"""`CalcJob` implementation to do a SCF calculation using Fireball."""

from copy import deepcopy

from aiida import orm

from aiida_fireball.calculations.base import BaseFireballCalculation


class ScfCalculation(BaseFireballCalculation):
    """`CalcJob` implementation to do a SCF calculation using Fireball."""

    # Blocked keywords that are to be specified in the subclass:
    _blocked_keywords = deepcopy(BaseFireballCalculation._blocked_keywords)
    _blocked_keywords["OPTION"]["nstepi"] = 1
    _blocked_keywords["OPTION"]["nstepf"] = 1
    _blocked_keywords["OPTION"]["ifixcharge"] = 0

    _default_symlink_usage = False

    @classmethod
    def define(cls, spec):
        """Define inputs and outputs of the calculation."""
        # yapf: disable
        super().define(spec)
        spec.input('metadata.options.parser_name', valid_type=str, default='fireball.scf')
        spec.inputs.validator = cls.validate_inputs

        spec.output('output_parameters', valid_type=orm.Dict,
            help='The `output_parameters` output node of the successful calculation.')
        spec.output('output_structure', valid_type=orm.StructureData, required=False,
            help='The `output_structure` output node of the successful calculation if present.')
        spec.output('output_trajectory', valid_type=orm.TrajectoryData, required=False)
        spec.output('output_band', valid_type=orm.BandsData, required=False,
            help='The `output_band` output node of the successful calculation if present.')
        spec.output('output_kpoints', valid_type=orm.KpointsData, required=False)
        spec.output('output_atomic_occupations', valid_type=orm.Dict, required=False)
        spec.default_output_node = 'output_parameters'

        # Unrecoverable errors: required retrieved files could not be read, parsed or are otherwise incomplete
        spec.exit_code(340, 'ERROR_OUT_OF_WALLTIME_INTERRUPTED',
            message='The calculation stopped prematurely because it ran out of walltime but the job was killed by the '
                    'scheduler before the files were safely written to disk for a potential restart.')
        spec.exit_code(350, 'ERROR_UNEXPECTED_PARSER_EXCEPTION',
            message='The parser raised an unexpected exception: {exception}')
