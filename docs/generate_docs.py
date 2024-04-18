"""
Write RST files for the CLI options and parser elements
"""

from pathlib import Path
import inspect
import textwrap
import argparse

from cms_perf.setup import cli_parser, cli

TARGET_DIR = Path(__file__).parent / "generated"
TARGET_DIR.mkdir(exist_ok=True)


def normalized_doc(obj: object) -> str:
    return textwrap.dedent(obj.__doc__ or "").strip()


def document_cli(*, sensors: bool) -> str:
    """Create the RST for all CLI sensor or other options"""
    rst_lines: "list[str]" = []
    for action in cli.CLI._actions:
        if (action.type != cli_parser.parse_sensor) == sensors:
            continue
        cli_name = max(action.option_strings, key=len)
        assert action.help is not None, "all CLI options must have a 'help' text"
        cli_help = (
            action.help + r" [default: %(default)s]"
            if r"%(default)s" not in action.help
            and action.default is not argparse.SUPPRESS
            else action.help
        )
        default = dict(default=f"``{action.default}``")
        rst_lines.append(f"``{cli_name}``\n   {cli_help % default}\n")
    return "\n".join(rst_lines)


def is_variadic(param: inspect.Parameter):
    return param.kind == inspect.Parameter.VAR_POSITIONAL


def document_cli_call(call_info: cli_parser.CallInfo) -> str:
    """Create the RST for a single CLI sensor or transformation"""
    rst_lines: "list[str]" = []
    parameters = inspect.signature(call_info.call).parameters
    parameters = {k: v for k, v in parameters.items() if k != "interval"}
    default_callable = all(
        param.default is not inspect.Parameter.empty or is_variadic(param)
        for param in parameters.values()
    )
    if default_callable:
        rst_lines.append(f"``{call_info.cli_name}``")
    if parameters:
        signature = ", ".join(
            f"{arg_name}{'...' if is_variadic(arg_stats) else ''}"
            for arg_name, arg_stats in parameters.items()
        )
        rst_lines.append(f"``{call_info.cli_name}({signature})``")
    assert rst_lines, f"{call_info.cli_name} must support one of defaults or parameters"
    rst_lines = [" or ".join(rst_lines)]
    assert getattr(call_info.call, "__doc__"), f"{call_info.cli_name} needs a __doc__"
    rst_lines.extend(
        f"   {line}" for line in normalized_doc(call_info.call).splitlines()
    )
    return "\n".join(rst_lines)


def document_cli_calls() -> str:
    """Create the RST for all CLI sensors and transformations"""
    rst_blocks: "list[str]" = []
    for call_info in sorted(
        cli_parser.KNOWN_CALLABLES.values(), key=lambda ci: ci.cli_name
    ):
        rst_blocks.append(document_cli_call(call_info))
    return "\n\n".join(rst_blocks)


with open(TARGET_DIR / "cli_sensors.rst", "w") as out_stream:
    out_stream.write(document_cli(sensors=True))


with open(TARGET_DIR / "cli_options.rst", "w") as out_stream:
    out_stream.write(document_cli(sensors=False))


with open(TARGET_DIR / "cli_callables.rst", "w") as out_stream:
    out_stream.write(document_cli_calls())
