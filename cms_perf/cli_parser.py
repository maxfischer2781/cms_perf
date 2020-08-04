from typing import TypeVar, Optional, Dict, NamedTuple, List, Callable, Tuple
from typing_extensions import Protocol
import inspect

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
    (*terms,) = result[0]
    return f"({' '.join(terms)})"


EXPRESSION = pp.infixNotation(
    (NUMBER | GENERATED),
    [
        (pp.oneOf(operators), 2, pp.opAssoc.LEFT, transpile_binop)
        for operators in ("* /", "+ -")
    ],
)


# Sensor Plugins
class Sensor(Protocol):
    def __call__(self, *args, **kwargs) -> float:
        ...


class SInfo(NamedTuple):
    call: Sensor
    cli_name: str
    cli_signature: List[str]


S = TypeVar("S", bound=Sensor)
SENSORS: Dict[str, SInfo] = {}  # transpiled_name => SFInfo


def compile_call(
    call_name: str,
    arity: int,
    transpiled_name: Optional[str] = None,
    extra_args: Tuple[str, ...] = (),
):
    """Compile a call with a given argument arity to a transpile expression"""
    transpiled_name = transpiled_name if transpiled_name is not None else call_name
    call_defaults = pp.Suppress(call_name)

    @call_defaults.setParseAction
    def transpile(result: pp.ParseResults) -> str:
        parameters = ", ".join(extra_args)
        return f"{transpiled_name}({parameters})"

    if arity > 0:
        signature = EXPRESSION
        for _ in range(arity - 1):
            signature = signature - pp.Suppress(",") - EXPRESSION
        call_params = (
            pp.Suppress(call_name) + pp.Suppress("(") - signature - pp.Suppress(")")
        )

        @call_params.setParseAction
        def transpile(result: pp.ParseResults) -> str:
            parameters = ", ".join(extra_args + tuple(result))
            return f"{transpiled_name}({parameters})"

        return call_params, call_defaults
    return (call_defaults,)


def cli_sensor(name: Optional[str] = None):
    """
    Register a sensor for the CLI with its own name or ``name``
    """
    assert not callable(name), "cli_sensor must be called before decorating"

    def register(call: S):
        _register_cli_sensor(call, name)
        return call

    return register


def _register_cli_sensor(call: S, cli_name: Optional[str] = None) -> S:
    cli_name = cli_name if cli_name is not None else call.__name__
    source_name = cli_name.replace(".", "_")
    assert source_name not in SENSORS, f"cannot re-register sensor {source_name}"
    raw_parameters = inspect.signature(call).parameters
    assert all(
        param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        for param in raw_parameters.values()
    ), "sensor factories may only take regular parameters"
    cli_parameters = [param for param in raw_parameters if param != "interval"]
    SENSORS[source_name] = SInfo(call, cli_name, cli_parameters)
    GENERATED << pp.MatchFirst(
        (
            *(GENERATED.expr.exprs if GENERATED.expr else ()),
            *compile_call(
                cli_name,
                len(cli_parameters),
                source_name,
                ("interval",) if "interval" in raw_parameters else (),
            ),
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
        f"lambda interval, {free_variables}: lambda: {py_source}",
        filename=name,
        mode="eval",
    )
    print(source, f"lambda {free_variables}: {py_source}")
    return eval(code, {}, {})


def compile_sensors(
    interval: float, *sensors: Callable[..., Callable[[], float]]
) -> List[Callable[[], float]]:
    raw_sensors = {name: sf_info.call for name, sf_info in SENSORS.items()}
    return [sensor(interval=interval, **raw_sensors) for sensor in sensors]
