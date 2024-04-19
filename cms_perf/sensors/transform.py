from ..setup.cli_parser import cli_call


@cli_call(name="max")
def maximum(a: float, b: float, *others: float) -> float:
    """The maximum value of all arguments"""
    return max(a, b, *others)


@cli_call(name="min")
def minimum(a: float, b: float, *others: float) -> float:
    """The minimum value of all arguments"""
    return min(a, b, *others)


@cli_call(name="relu")
def just_relu(value: float, bias: float) -> float:
    """Reduce ``value`` by ``bias`` and truncate results below 0. Equivalent to ``max(value-bias, 0)``."""
    return max(value - bias, 0)


@cli_call(name="relun")
def normalized_relu(value: float, bias: float) -> float:
    """Truncate ``value`` below ``bias`` to 0 and normalize the result. This effectively remaps the range ``bias``..100 to 0..100."""
    if bias >= 100 or bias >= value:
        return 0
    return (value - bias) * 100 / (100 - bias)
