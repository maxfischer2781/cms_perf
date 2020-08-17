from pathlib import Path

from cms_perf import cli


TARGET_DIR = Path(__file__).parent / 'generated'
TARGET_DIR.mkdir(exist_ok=True)


def document_cli_sensors():
    rst_lines = []
    for action in cli.CLI._actions:
        if action.type != cli.cli_parser.parse_sensor:
            continue
        cli_name = max(action.option_strings, key=len)
        rst_lines.append(
            f"`{cli_name}={action.default}`\n"
            + f"   {action.help}\n"
        )
    return '\n'.join(rst_lines)


with open(TARGET_DIR / 'cli_sensors.rst', 'w') as out_stream:
    out_stream.write(document_cli_sensors())
