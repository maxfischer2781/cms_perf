from pathlib import Path
import inspect
import textwrap

from cms_perf.setup import cli_parser, cli

TARGET_DIR = Path(__file__).parent / "generated"
TARGET_DIR.mkdir(exist_ok=True)


def normalized_doc(obj):
    return textwrap.dedent(obj.__doc__).strip()


def document_cli_sensors():
    rst_lines = []
    for action in cli.CLI._actions:
        if action.type != cli_parser.parse_sensor:
            continue
        cli_name = max(action.option_strings, key=len)
        rst_lines.append(f"``{cli_name}={action.default}``\n   {action.help}\n")
    return "\n".join(rst_lines)


def is_variadic(param: inspect.Parameter):
    return param.kind == inspect.Parameter.VAR_POSITIONAL


def document_cli_call(call_info: cli_parser.CallInfo) -> str:
    rst_lines = []
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


def document_cli_calls():
    rst_blocks = []
    for call_info in sorted(
        cli_parser.KNOWN_CALLABLES.values(), key=lambda ci: ci.cli_name
    ):
        rst_blocks.append(document_cli_call(call_info))
    return "\n\n".join(rst_blocks)


with open(TARGET_DIR / "cli_sensors.rst", "w") as out_stream:
    out_stream.write(document_cli_sensors())


with open(TARGET_DIR / "cli_callables.rst", "w") as out_stream:
    out_stream.write(document_cli_calls())
