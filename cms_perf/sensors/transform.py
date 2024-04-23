import math

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
    """
    Reduce ``value`` by ``bias`` and truncate below 0, as ``max(value-bias, 0)``
    """
    return max(value - bias, 0)


@cli_call(name="relun")
def normalized_relu(value: float, bias: float) -> float:
    """
    Truncate ``value`` below ``bias`` to 0 and normalize the result

    This effectively remaps the range ``bias``..100 to 0..100.
    Useful to ignore low load situations in which differences are incosequential.
    """
    if bias >= 100 or bias >= value:
        return 0
    return (value - bias) * 100 / (100 - bias)


@cli_call(name="erf")
def just_erf(value: float) -> float:
    """The error function mapping -inf..inf to -1..1. See :py:func:`math.erf`"""
    return math.erf(value)


ERF2PCT_FACTOR = (100 - 0) / (math.erf(2) - math.erf(-2))


@cli_call(name="sigmoid")
def normalized_erf(value: float) -> float:
    """
    A sigmoid boosting changes around 50, similar to a normalized error function

    Applying ``sigmoid`` to the range 0..100 compresses the low and high ranges
    (0..25 and 75..100) but expands the medium range (25..75). For load balancing,
    this means load around 50 is preferred and the most sensitive to differences.
    """
    if value >= 100:
        return 100
    elif value <= 0:
        return 0
    # Note on range: erf(2) == 0.995 ~= 1
    # map value from 0...100 to -2..2
    erf_value = value / 25 - 2
    erf_result = math.erf(erf_value)
    # map erf from -erf(2)...erf(2) to 0...100
    return (erf_result * ERF2PCT_FACTOR) + 50
