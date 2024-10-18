"""Parser implementation for the ScfCalculation calculation job class."""

import re
from typing import Optional, Tuple

from aiida import orm
from aiida.common import AttributeDict
from aiida.engine import ExitCode
from aiida.parsers import Parser

from . import get_logging_container
from .parse_raw import parse_raw_stdout


class ScfParser(Parser):
    """`Parser` implementation for the `ScfCalculation` calculation job class."""

    success_string = "FIREBALL RUNTIME"

    def parse(self, **kwargs) -> ExitCode | None:
        """Parse outputs and store results in the database."""
        logs = get_logging_container()

        # Parse the stdout content
        parsed_data, logs = self.parse_stdout(logs)
        self.emit_logs(logs, ignore=None)
        self.out("output_parameters", orm.Dict(parsed_data))

    def parse_stdout(self, logs: AttributeDict) -> Tuple[str, dict, AttributeDict]:
        """Parse the stdout content of a Fireball SCF calculation."""
        output_filename = self.node.get_option("output_filename")

        if output_filename not in self.retrieved.base.repository.list_object_names():
            logs.error.append("ERROR_OUTPUT_STDOUT_MISSING")
            return "", {}, logs

        try:
            with self.retrieved.open(output_filename, "r") as handle:
                stdout = handle.read()
        except OSError as exception:
            logs.error.append("ERROR_OUTPUT_STDOUT_READ")
            logs.error.append(exception)
            return "", {}, logs

        try:
            parsed_data, logs = self._parse_stdout_base(stdout, logs)
        except Exception as exception:
            logs.error.append("ERROR_OUTPUT_STDOUT_PARSE")
            logs.error.append(exception)
            return stdout, {}, logs

        return parsed_data, logs

    @classmethod
    def _parse_stdout_base(cls, stdout: str, logs: AttributeDict) -> Tuple[dict, AttributeDict]:
        """
        This function only checks for basic content like FIREBALL RUNTIME

        :param stdout: the stdout content as a string.
        :returns: tuple of two dictionaries, with the parsed data and log messages, respectively.
        """

        if not re.search(cls.success_string, stdout):
            logs.error.append("ERROR_OUTPUT_STDOUT_INCOMPLETE")

        parsed_data = parse_raw_stdout(stdout)

        return parsed_data, logs

    def emit_logs(
        self, logs: list[AttributeDict] | tuple[AttributeDict] | AttributeDict, ignore: Optional[list]
    ) -> None:
        """Emit the messages in one or multiple "log dictionaries" through the logger of the parser.

        A log dictionary is expected to have the following structure: each key must correspond to a log level of the
        python logging module, e.g. `error` or `warning` and its values must be a list of string messages. The method
        will loop over all log dictionaries and emit the messages it contains with the log level indicated by the key.

        Example log dictionary structure::

            logs = {
                'warning': ['Could not parse the `etot_threshold` variable from the stdout.'],
                'error': ['Self-consistency was not achieved']
            }

        :param logs: log dictionaries
        :param ignore: list of log messages to ignore
        """
        ignore = ignore or []

        if not isinstance(logs, (list, tuple)):
            logs = [logs]

        for logs in logs:
            for level, messages in logs.items():
                for message in messages:
                    stripped = message.strip()

                    if stripped in ignore:
                        continue

                    getattr(self.logger, level)(stripped)
