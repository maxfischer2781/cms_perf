from pathlib import Path
import inspect

from cms_perf import cli
from cms_perf import cli_parser


TARGET_DIR = Path(__file__).parent / "generated"
TARGET_DIR.mkdir(exist_ok=True)


def document_cli_sensors():
    rst_lines = []
    for action in cli.CLI._actions:
        if action.type != cli.cli_parser.parse_sensor:
            continue
        cli_name = max(action.option_strings, key=len)
        rst_lines.append(f"``{cli_name}={action.default}``\n   {action.help}\n")
    return "\n".join(rst_lines)


def document_cli_call(call_info: cli_parser.CallInfo) -> str:
    rst_lines = []
    parameters = inspect.signature(call_info.call).parameters
    parameters = {k: v for k, v in parameters.items() if k != "interval"}
    default_callable = all(
        param.default is not inspect.Parameter.empty
        or param.kind == inspect.Parameter.VAR_POSITIONAL
        for param in parameters.values()
    )
    if default_callable:
        rst_lines.append(f"``{call_info.cli_name}``")
    if parameters:
        signature = ", ".join(f"{arg_name}" for arg_name in parameters)
        rst_lines.append(f"``{call_info.cli_name}({signature})``")
    assert rst_lines, f"{call_info.cli_name} must support one of defaults or parameters"
    assert getattr(call_info.call, "__doc__"), f"{call_info.cli_name} needs a __doc__"
    rst_lines.extend(f"\t{line}" for line in call_info.call.__doc__.splitlines())
    return "\n".join(rst_lines)


def document_cli_calls():
    rst_blocks = []
    for call_info in cli_parser.KNOWN_CALLABLES.values():
        rst_blocks.append(document_cli_call(call_info))
    return "\n\n".join(rst_blocks)


with open(TARGET_DIR / "cli_sensors.rst", "w") as out_stream:
    out_stream.write(document_cli_sensors())


with open(TARGET_DIR / "cli_callables.rst", "w") as out_stream:
    out_stream.write(document_cli_calls())
