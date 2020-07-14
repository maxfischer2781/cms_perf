from typing import List
import itertools
import subprocess
import sys


def capture(command: List[str], num_lines=5) -> List[bytes]:
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    output = list(itertools.islice(process.stdout, num_lines))
    if process.poll() is not None:
        output = b"\n".join(itertools.chain(output, process.stdout))
        print(output, file=sys.stderr)
        raise subprocess.CalledProcessError(
            returncode=process.poll(),
            cmd=command,
            output=b"\n".join(itertools.chain(output, process.stdout)),
        )
    process.terminate()
    return output
