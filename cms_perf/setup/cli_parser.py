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
from typing import TypeVar, Optional, Dict, NamedTuple, List, Callable, Type
from typing_extensions import Protocol
import inspect
import enum

import pyparsing as pp

pp.ParserElement.enablePackrat()


# Auto-generated expressions
GENERATED = pp.Forward().setName("TERM")


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
).setName('(NUMBER | TERM), [ ("*" | "/" | "+" | "-"), (NUMBER | TERM | EXPRESSION)]')


def parse(code: str) -> str:
    """Parse a CLI code string to Python source code"""
    try:
        return EXPRESSION.parseString(code, parseAll=True)[0]
    except pp.ParseException as pe:
        raise SyntaxError(
            str(pe), ("<cms_perf.cli_parser code>", pe.col, pe.loc, code)
        ) from None


# Sensor Plugins
class CLICall(Protocol):
    """A callable that can be registered for the CLI to provide values"""

    def __call__(self, *args, **kwargs) -> float:
        ...


class Transform(Protocol):
    """A callable that can be registered for the CLI to transform values"""

    def __call__(self, *args: float) -> float:
        ...


S = TypeVar("S", bound=CLICall)


class CallInfo(NamedTuple):
    call: Callable[..., float]
    cli_name: str


class DomainInfo(NamedTuple):
    domain: type
    cli_name: str
    parser: pp.ParserElement


# transpiled_name => CallInfo
KNOWN_CALLABLES: Dict[str, CallInfo] = {}
KNOWN_DOMAINS: Dict[str, DomainInfo] = {}

KNOWN_DOMAINS_MAP: Dict[type, DomainInfo] = {}


# automatic parser generation
def _extend_generated(*rules, base=GENERATED):
    base << pp.MatchFirst((*(base.expr.exprs if base.expr else ()), *rules))


_COMPILEABLE_PARAMETERS = (
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
    inspect.Parameter.VAR_POSITIONAL,
)

LEFT_PAR = pp.Suppress("(").setName('"("')
RIGHT_PAR = pp.Suppress(")").setName('")"')


def _compile_parameter(parameter: inspect.Parameter):
    annotation = parameter.annotation
    if annotation not in (float, inspect.Parameter.empty):
        assert annotation in KNOWN_DOMAINS_MAP, f"unknown CLI domain {annotation}"
        domain_info = KNOWN_DOMAINS_MAP[annotation]
        return domain_info.parser.copy().setName(
            f"{parameter.name}={domain_info.cli_name}"
        )
    return EXPRESSION.copy().setName(f"{parameter.name}=TERM")


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
        default_call = pp.Suppress(call_name).setName(f'"{call_name}"')

        @default_call.setParseAction
        def transpile_default(result: pp.ParseResults) -> str:
            arguments = "interval" if implicit_interval else ""
            return f"{transpiled_name}({arguments})"

        transpilers.append(default_call)
    if len(parameters):
        argument_parsers = []
        for parameter in parameters.values():
            if parameter.kind != inspect.Parameter.VAR_POSITIONAL:
                if argument_parsers:
                    argument_parsers.append(pp.Suppress(","))
                argument_parsers.append(_compile_parameter(parameter))
            else:
                param_parser = pp.delimitedList(_compile_parameter(parameter))
                if argument_parsers:
                    argument_parsers.append(
                        pp.Optional(pp.Suppress(",") - param_parser)
                    )
                else:
                    argument_parsers.append(pp.Optional(param_parser))
        signature = pp.And((LEFT_PAR, *argument_parsers, RIGHT_PAR))
        parameter_call = pp.Suppress(call_name).setName(f'"{call_name}"') + signature

        @parameter_call.setParseAction
        def transpile_with_args(result: pp.ParseResults) -> str:
            arguments = ("interval, " if implicit_interval else "") + ", ".join(result)
            return f"{transpiled_name}({arguments})"

        transpilers.append(parameter_call)
    return transpilers[::-1]


# registration decorators
def cli_call(name: Optional[str] = None):
    """
    Register a sensor or transformation for the CLI with its own name or ``name``
    """
    assert not callable(name), "cli_call must be called before decorating"

    def register(call: S) -> S:
        _register_cli_callable(call, name)
        return call

    return register


def _register_cli_callable(call: S, cli_name: Optional[str]) -> S:
    cli_name = cli_name if cli_name is not None else call.__name__
    source_name = cli_name.replace(".", "_")
    assert (
        source_name not in KNOWN_CALLABLES
    ), f"cannot re-register CLI callable {source_name}"
    KNOWN_CALLABLES[source_name] = CallInfo(call, cli_name)
    _extend_generated(*_compile_cli_call(cli_name, source_name, call))
    return call


TP = TypeVar("TP", bound=type)


def cli_domain(name: Optional[str] = None):
    """
    Register a value domain for the CLI displayed with its own name or ``name``
    """

    def register(domain: TP) -> TP:
        if issubclass(domain, enum.Enum):
            _register_enum(domain, name)
        else:
            raise TypeError(f"Cannot register CLI domain: {domain}")
        return domain

    return register


def _register_enum(domain: Type[enum.Enum], cli_name: Optional[str]):
    cli_name = cli_name if cli_name is not None else domain.__name__
    source_name = cli_name.replace(".", "_")
    assert (
        source_name not in KNOWN_DOMAINS
    ), f"cannot re-register CLI domain {source_name}"
    cases = sorted(domain.__members__, reverse=True)
    match_case = pp.MatchFirst(tuple(map(pp.Keyword, cases))).setName(
        " | ".join(f'"{case}"' for case in cases)
    )

    @match_case.setParseAction
    def transpile_enum_case(result: pp.ParseResults):
        (case,) = result
        return f"{source_name}['{case}']"

    KNOWN_DOMAINS_MAP[domain] = KNOWN_DOMAINS[source_name] = DomainInfo(
        domain, cli_name, match_case
    )


# digesting of CLI information
def parse_sensor(
    source: str, name: Optional[str] = None
) -> Callable[..., Callable[[], float]]:
    py_source = parse(source)
    name = (
        name
        if name is not None
        else f"<cms_perf.cli_parser code {source!r} => {py_source!r}>"
    )
    pp.ParserElement.resetCache()  # free parser cache
    free_variables = ", ".join(KNOWN_CALLABLES.keys() | KNOWN_DOMAINS.keys())
    code = compile(
        f"lambda interval, {free_variables}: lambda: {py_source}",
        filename=name,
        mode="eval",
    )
    return eval(code, {}, {})


def compile_sensors(
    interval: float, *sensors: Callable[..., Callable[[], float]]
) -> List[Callable[[], float]]:
    raw_sensors = {name: sf_info.call for name, sf_info in KNOWN_CALLABLES.items()}
    raw_domains = {name: dm_info.domain for name, dm_info in KNOWN_DOMAINS.items()}
    return [
        factory(interval=interval, **raw_sensors, **raw_domains) for factory in sensors
    ]


# CLI transformations
@cli_call(name="max")
def maximum(a, b, *others):
    """The maximum value of all arguments"""
    return max(a, b, *others)


@cli_call(name="min")
def minimum(a, b, *others):
    """The minimum value of all arguments"""
    return min(a, b, *others)


if __name__ == "__main__":
    # provide debug information on the parser
    from ..sensors import sensor, net_load, xrd_load  # noqa
    from . import cli_parser  # noqa

    print("EXPRESSION:", cli_parser.EXPRESSION)
    print("TERM:", cli_parser.GENERATED.expr)
    for domain in cli_parser.KNOWN_DOMAINS.values():
        print(f"{domain.cli_name}: {domain.parser}")
