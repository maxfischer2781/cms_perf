"""
Parser to allow configuration, basic math and transformation on sensors via the CLI

The syntax is loosely speaking:
* float math including ``*``, ``/``, ``+``, ``-`` and parentheses
* calls with and without arguments
* constants such as enums
and everything compiles down to Python source code.

The math part is an explicitly defined infix parser rule.
The parts for both calls and constants are automatically generated from Python objects.
"""

from typing import TypeVar, Optional, Dict, NamedTuple, List, Callable, Type
import inspect
import enum

import pyparsing as pp

pp.ParserElement.enablePackrat()


# Auto-generated expressions
GENERATED: pp.Forward = pp.Forward().setName("TERM")  # type: ignore


# Number literals – float should be precise enough for everything
NUMBER = pp.Regex(r"-?\d+\.?\d*").setName("NUMBER")


@NUMBER.setParseAction  # type: ignore
def transpile(result: pp.ParseResults) -> str:
    """Capture float literals directly"""
    return result[0]  # type: ignore


# Mathematical Operators
def transpile_binop(result: pp.ParseResults) -> str:
    """Capture binary operations such as ``12 * b`` and add precedence via ``()``"""
    terms = list(result[0])  # type: ignore
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
        return EXPRESSION.parseString(code, parseAll=True)[0]  # type: ignore
    except pp.ParseException as pe:
        raise SyntaxError(
            str(pe), ("<cms_perf.cli_parser code>", pe.col, pe.loc, code)
        ) from None


# Sensor Plugins
CLICall = Callable[..., float]


S = TypeVar("S", bound=CLICall)


class CallInfo(NamedTuple):
    """Information for running `cli_name(...)` via `call`"""

    call: Callable[..., float]
    cli_name: str


class DomainInfo(NamedTuple):
    """Information for translating literal of `cli_name` in a type `domain`"""

    domain: type
    cli_name: str
    parser: pp.ParserElement


# transpiled_name => CallInfo
KNOWN_CALLABLES: Dict[str, CallInfo] = {}
KNOWN_DOMAINS: Dict[str, DomainInfo] = {}

KNOWN_DOMAINS_MAP: Dict[type, DomainInfo] = {}


# automatic parser generation
def _extend_generated(*rules: pp.ParserElement, base: pp.Forward = GENERATED):
    base <<= pp.MatchFirst(
        (*(base.expr.exprs if base.expr else ()), *rules)  # type:ignore
    )


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


def _compile_cli_call(
    call_name: str, transpiled_name: str, call: CLICall
) -> "list[pp.ParserElement]":
    """Compile a call with a given argument arity to a transpile expression"""
    transpilers: "list[pp.ParserElement]" = []
    parameters = inspect.signature(call).parameters
    implicit_interval = "interval" in parameters
    if implicit_interval:
        assert (
            next(iter(parameters)) == "interval"
        ), "interval must be the first parameter"
        parameters = {k: v for k, v in parameters.items() if k != "interval"}
    for parameter in parameters.values():
        assert parameter.kind in _COMPILEABLE_PARAMETERS, f"Cannot compile {parameter}"
    # if all parameters are optional, allow call without arguments
    if all(
        param.default is not inspect.Parameter.empty
        or param.kind == inspect.Parameter.VAR_POSITIONAL
        for param in parameters.values()
    ):
        default_call = pp.Suppress(call_name).setName(f'"{call_name}"')

        @default_call.setParseAction  # type: ignore
        def transpile_default(result: pp.ParseResults) -> str:  # type: ignore[reportUnusedFunction]
            arguments = "interval" if implicit_interval else ""
            return f"{transpiled_name}({arguments})"

        transpilers.append(default_call)
    # if parameters may be passed, allow call with parametrised arguments
    if len(parameters):
        argument_parsers: "list[pp.ParserElement]" = []
        for parameter in parameters.values():
            # individual parameter
            if parameter.kind != inspect.Parameter.VAR_POSITIONAL:
                if argument_parsers:
                    argument_parsers.append(pp.Suppress(","))
                argument_parsers.append(_compile_parameter(parameter))
            # variadic parameter, compile to a list of parameters
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

        @parameter_call.setParseAction  # type: ignore
        def transpile_with_args(result: pp.ParseResults) -> str:  # type: ignore[reportUnusedFunction]
            arguments = ("interval, " if implicit_interval else "") + ", ".join(result)
            return f"{transpiled_name}({arguments})"

        transpilers.append(parameter_call)
    return transpilers[::-1]


# registration decorators
def cli_call(name: Optional[str] = None) -> Callable[[S], S]:
    """
    Register a sensor or transformation for the CLI with its own name or ``name``
    """
    assert not callable(name), "cli_call must be called before decorating"

    def register(call: S) -> S:
        _register_cli_callable(call, name)
        return call

    return register


def _register_cli_callable(call: S, cli_name: Optional[str]) -> S:
    cli_name = cli_name if cli_name is not None else call.__name__  # type: ignore
    assert isinstance(cli_name, str)
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
            raise TypeError(f"Can only register Enum domain, not {domain}")
        return domain  # type: ignore

    return register


def _register_enum(domain: Type[enum.Enum], cli_name: Optional[str]):
    cli_name = cli_name if cli_name is not None else domain.__name__
    source_name = cli_name.replace(".", "_")
    assert source_name not in KNOWN_DOMAINS, (
        f"cannot re-register CLI domain {source_name}"
        f" as {domain.__module__}:{domain.__qualname__}"
    )
    cases = sorted(domain.__members__, reverse=True)
    match_case = pp.MatchFirst(tuple(map(pp.Keyword, cases))).setName(
        " | ".join(f'"{case}"' for case in cases)
    )

    @match_case.setParseAction  # type: ignore
    def transpile_enum_case(result: pp.ParseResults) -> str:  # type: ignore[reportUnusedFunction]
        case: str = result[0]  # type: ignore
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
    raw_domains = {name: dm_info.domain for name, dm_info in KNOWN_DOMAINS.items()}  # type: ignore[reportUnknownMemberType]
    return [
        factory(interval=interval, **raw_sensors, **raw_domains) for factory in sensors
    ]


if __name__ == "__main__":
    # provide debug information on the parser
    from ..sensors import sensor, xrd_load  # noqa  # pyright: ignore
    from . import cli_parser  # noqa

    print("EXPRESSION:", cli_parser.EXPRESSION)
    print("TERM:", cli_parser.GENERATED.expr)
    for domain in cli_parser.KNOWN_DOMAINS.values():
        print(f"{domain.cli_name}: {domain.parser}")
