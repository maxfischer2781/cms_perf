"""
Parser to allow configuration, basic math and transformation on sensors via the CLI

The syntax is loosely speaking:
* float math including ``*``, ``/``, ``+``, ``-`` and parentheses
* calls with and without arguments
* constants such as enums
and everything compiles down to Python source code.

The math part is an explicitly defined.
Both calls and constants are automatically generated from Python objects.
"""
from typing import TypeVar, Optional, Dict, NamedTuple, List, Callable
from typing_extensions import Protocol
import inspect

import pyparsing as pp

pp.ParserElement.enablePackrat()


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


def parse(code: str) -> str:
    """Parse a CLI code string to Python source code"""
    try:
        return EXPRESSION.parseString(code, parseAll=True)[0]
    except pp.ParseException as pe:
        raise SyntaxError(
            str(pe), ("<cms_perf.cli_parser code>", pe.col, pe.loc, code)
        ) from None


# Sensor Plugins
class Sensor(Protocol):
    """A sensor that can be registered for the CLI to provide values"""

    def __call__(self, *args, **kwargs) -> float:
        ...


class Transform(Protocol):
    """A callable that can be registered for the CLI to transform values"""

    def __call__(self, *args: float) -> float:
        ...


S = TypeVar("S", bound=Sensor)
CT = TypeVar("CT", bound=Transform)


class CallInfo(NamedTuple):
    call: Callable[..., float]
    cli_name: str


# transpiled_name => CallInfo
TRANSFORMS: Dict[str, CallInfo] = {}
SENSORS: Dict[str, CallInfo] = {}


# automatic parser generation
_COMPILEABLE_PARAMETERS = (
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
    inspect.Parameter.VAR_POSITIONAL,
)


def _compile_cli_call(call_name: str, transpiled_name: str, call: Callable):
    """Compile a call with a given argument arity to a transpile expression"""
    transpilers = []
    parameters = inspect.signature(call).parameters
    implicit_interval = "interval" in parameters
    if implicit_interval:
        assert next(iter(parameters)) == "interval", "interval must be first"
        parameters = {k: v for k, v in parameters.items() if k != "interval"}
    for parameter in parameters.values():
        assert parameter.kind in _COMPILEABLE_PARAMETERS, f"Cannot compile {parameter}"
    if all(
        param.default is not inspect.Parameter.empty
        or param.kind == inspect.Parameter.VAR_POSITIONAL
        for param in parameters.values()
    ):
        default_call = pp.Suppress(call_name)

        @default_call.setParseAction
        def transpile_default(result: pp.ParseResults) -> str:
            arguments = "interval" if implicit_interval else ""
            return f"{transpiled_name}({arguments})"

        transpilers.append(default_call)
    if len(parameters):
        argument_parsers = []
        for parameter in parameters.values():
            if argument_parsers:
                argument_parsers.append(pp.Suppress(","))
            if parameter.kind != inspect.Parameter.VAR_POSITIONAL:
                argument_parsers.append(EXPRESSION)
            else:
                argument_parsers.append(pp.Optional(pp.delimitedList(EXPRESSION)))
        signature = pp.And((pp.Suppress("("), *argument_parsers, pp.Suppress(")")))
        parameter_call = pp.Suppress(call_name) + signature

        @parameter_call.setParseAction
        def transpile_with_args(result: pp.ParseResults) -> str:
            arguments = ("interval, " if implicit_interval else "") + ", ".join(result)
            return f"{transpiled_name}({arguments})"

        transpilers.append(parameter_call)
    return transpilers[::-1]


# registration decorators
# These are practically the same, but types differ and we may need to do
# additional pre-processing for each in the future.
def cli_transform(name: Optional[str] = None):
    """
    Register a transformation for the CLI with its own name or ``name``
    """
    assert not callable(name), "cli_transform must be called before decorating"

    def register(call: CT) -> CT:
        _register_cli_callable(call, name, TRANSFORMS)
        return call

    return register


def cli_sensor(name: Optional[str] = None):
    """
    Register a sensor for the CLI with its own name or ``name``
    """
    assert not callable(name), "cli_sensor must be called before decorating"

    def register(call: S) -> S:
        _register_cli_callable(call, name, SENSORS)
        return call

    return register


def _register_cli_callable(
    call: S, cli_name: Optional[str], target: Dict[str, CallInfo]
) -> S:
    cli_name = cli_name if cli_name is not None else call.__name__
    source_name = cli_name.replace(".", "_")
    assert source_name not in target, f"cannot re-register CLI callable {source_name}"
    target[source_name] = CallInfo(call, cli_name)
    GENERATED << pp.MatchFirst(
        (
            *(GENERATED.expr.exprs if GENERATED.expr else ()),
            *_compile_cli_call(cli_name, source_name, call,),
        )
    )
    return call


# digesting of CLI information
def parse_sensor(
    source: str, name: Optional[str] = None
) -> Callable[..., Callable[[], float]]:
    name = name if name is not None else f"<cms_perf.cli_parser code {source!r}>"
    py_source = parse(source)
    pp.ParserElement.resetCache()  # free parser cache
    free_variables = ", ".join(SENSORS.keys() | TRANSFORMS.keys())
    code = compile(
        f"lambda interval, {free_variables}: lambda: {py_source}",
        filename=name,
        mode="eval",
    )
    return eval(code, {}, {})


def compile_sensors(
    interval: float, *sensors: Callable[..., Callable[[], float]]
) -> List[Callable[[], float]]:
    raw_sensors = {
        name: sf_info.call for name, sf_info in (*SENSORS.items(), *TRANSFORMS.items())
    }
    return [sensor(interval=interval, **raw_sensors) for sensor in sensors]


# CLI transformations
@cli_transform(name="max")
def maximum(*operands):
    return max(operands)


@cli_transform(name="min")
def minimum(*operands):
    return min(operands)
