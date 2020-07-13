from typing import List
import itertools
import subprocess


def capture(command: List[str], num_lines=5) -> List[bytes]:
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    output = list(itertools.islice(process.stdout, num_lines))
    process.terminate()
    return output
