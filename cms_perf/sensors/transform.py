from ..setup.cli_parser import cli_call


@cli_call(name="max")
def maximum(a: float, b: float, *others: float) -> float:
    """The maximum value of all arguments"""
    return max(a, b, *others)


@cli_call(name="min")
def minimum(a: float, b: float, *others: float) -> float:
    """The minimum value of all arguments"""
    return min(a, b, *others)


@cli_call(name="nrelu")
def normalized_relu(x: float, bias: float) -> float:
    """The minimum value of all arguments"""
    if bias >= 100:
        return 0
    if x < bias:
        return 0
    return (x - bias) * 100 / (100 - bias)
