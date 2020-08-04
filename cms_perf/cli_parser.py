from typing import TypeVar, Optional, Dict, NamedTuple, List, Callable
from typing_extensions import Protocol
import functools
import inspect
import itertools

import pyparsing as pp


# Auto-generated expressions
GENERATED = pp.Forward()


# Number literals – float should be precise enough for everything
NUMBER = pp.Regex(r"-?\d+\.?\d*").setName("NUMBER")


@NUMBER.setParseAction
def transpile(result: pp.ParseResults) -> str:
    return result[0]


# Mathematical Operators
def transpile_binop(result: pp.ParseResults):
    lhs, operator, rhs = result[0]
    return f"({lhs} {operator} {rhs})"


EXPRESSION = pp.infixNotation(
    (NUMBER | GENERATED), [(pp.oneOf("+ * - /"), 2, pp.opAssoc.LEFT, transpile_binop)]
)


# Sensor Plugins
class Sensor(Protocol):
    def __call__(self) -> float:
        ...


class SensorFactory(Protocol):
    def __call__(self, interval, *args, **kwargs) -> Sensor:
        ...


class SFInfo(NamedTuple):
    factory: SensorFactory
    cli_signature: List[str]


SF = TypeVar("SF", bound=SensorFactory)
SENSORS: Dict[str, SFInfo] = {}


def compile_call(call_name: str, arity: int, transpiled_name: Optional[str] = None):
    """Compile a call with a given argument arity to a transpile expression"""
    transpiled_name = transpiled_name if transpiled_name is not None else call_name
    call_defaults = pp.Suppress(call_name)

    @call_defaults.setParseAction
    def transpile(result: pp.ParseResults) -> str:
        return f"{transpiled_name}()"

    if arity > 0:
        signature = EXPRESSION
        for _ in range(arity - 1):
            signature = signature - pp.Suppress(",") - EXPRESSION
        call_params = (
            pp.Suppress(call_name) + pp.Suppress("(") - signature - pp.Suppress(")")
        )

        @call_params.setParseAction
        def transpile(result: pp.ParseResults) -> str:
            parameters = ", ".join(result)
            return f"{transpiled_name}({parameters})"

        return call_params, call_defaults
    return (call_defaults,)


def cli_sensor(call: Optional[SF] = None, *, name: Optional[str] = None):
    """
    Register a sensor factory for the CLI with its own name or ``name``
    """
    if call is None:
        return functools.partial(cli_sensor, name=name)
    return _cli_sensor(call, name)


def _cli_sensor(call: SF, name: Optional[str] = None) -> SF:
    name = name if name is not None else call.__name__
    assert name not in SENSORS, f"cannot re-register sensor {name}"
    raw_parameters = inspect.signature(call).parameters
    assert (
        "interval" in raw_parameters
    ), f"sensor factory {name!r} must accept an 'interval'"
    assert all(
        param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        for param in raw_parameters.values()
    ), "sensor factories may only take regular parameters"
    cli_parameters = list(
        itertools.dropwhile(lambda param: param != "interval", raw_parameters)
    )
    SENSORS[name] = SFInfo(call, cli_parameters)
    GENERATED << pp.MatchFirst(
        (
            *(GENERATED.expr.exprs if GENERATED.expr else ()),
            *compile_call(name, len(cli_parameters)),
        )
    )
    return call


def prepare_sensor(
    source: str, name: Optional[str] = None
) -> Callable[..., Callable[[], float]]:
    name = name if name is not None else f"<cms_perf.cli_parser code {source!r}>"
    free_variables = ", ".join(SENSORS)
    (py_source,) = EXPRESSION.parseString(source, parseAll=True)
    code = compile(
        f"lambda {free_variables}: lambda: {py_source}", filename=name, mode="eval"
    )
    print(source, f"lambda {free_variables}: {py_source}")
    return eval(code, {}, {})


def compile_sensors(
    interval: float, *sensors: Callable[..., Callable[[], float]]
) -> List[Callable[[], float]]:
    raw_sensors = {name: sf_info.factory(interval) for name, sf_info in SENSORS.items()}
    return [sensor(**raw_sensors) for sensor in sensors]
