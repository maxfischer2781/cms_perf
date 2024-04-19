from ..setup.cli_parser import cli_call


@cli_call(name="max")
def maximum(a: float, b: float, *others: float) -> float:
    """The maximum value of all arguments"""
    return max(a, b, *others)


@cli_call(name="min")
def minimum(a: float, b: float, *others: float) -> float:
    """The minimum value of all arguments"""
    return min(a, b, *others)
