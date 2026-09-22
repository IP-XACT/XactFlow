import ipxact
import pytest

from xactflow.expressions import ExpressionError, evaluate, parameter_resolver


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("42", 42),
        ("0", 0),
        ("1_000", 1000),
        ("0x1F", 31),
        ("0X1f", 31),
        ("0x00FF", 255),
        ("8'hFF", 255),
        ("4'b1010", 10),
        ("3'o7", 7),
        ("8'd100", 100),
        ("'h1F", 31),
        ("3.14", 3.14),
        ("1e10", 1e10),
        ("1.5e-3", 0.0015),
    ],
)
def test_literals(expression, expected):
    assert evaluate(expression) == expected


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("4'shF", -1),
        ("8'shFF", -1),
        ("4'sh7", 7),
        ("'shFFFFFFFF", -1),
    ],
)
def test_signed_sized_literals_use_twos_complement(expression, expected):
    assert evaluate(expression) == expected


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("2+3*4", 14),
        ("(2+3)*4", 20),
        ("2**3**2", 512),  # right-associative: 2**(3**2)
        ("-2**2", 4),  # unary binds tighter than ** in SystemVerilog, unlike Python
        ("2-3-4", -5),  # left-associative
    ],
)
def test_arithmetic_precedence_and_associativity(expression, expected):
    assert evaluate(expression) == expected


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("-7/2", -3),  # truncates toward zero, not Python's floor division (-4)
        ("7/-2", -3),
        ("7/2", 3),
        ("-7 % 2", -1),  # result takes the sign of the dividend
        ("7 % -2", 1),
    ],
)
def test_integer_division_and_modulo_truncate_toward_zero(expression, expected):
    assert evaluate(expression) == expected


def test_division_by_zero_raises():
    with pytest.raises(ExpressionError, match="division by zero"):
        evaluate("1/0")


def test_modulo_by_zero_raises():
    with pytest.raises(ExpressionError, match="modulo by zero"):
        evaluate("1 % 0")


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("0xF0 & 0x0F", 0),
        ("0xF0 | 0x0F", 255),
        ("0xFF ^ 0x0F", 0xF0),
        ("5 & 3", 1),
        ("1 << 4", 16),
        ("256 >> 4", 16),
        ("~0 & 0xFF", 255),
    ],
)
def test_bitwise_operators(expression, expected):
    assert evaluate(expression) == expected


def test_bitwise_operator_on_a_float_operand_raises():
    with pytest.raises(ExpressionError, match="requires an integer operand"):
        evaluate("3.5 & 2")


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("3 < 5", 1),
        ("5 <= 5", 1),
        ("5 > 3", 1),
        ("5 >= 6", 0),
        ("3 == 3", 1),
        ("3 != 4", 1),
        ("1 && 0", 0),
        ("1 && 1", 1),
        ("0 || 1", 1),
        ("0 || 0", 0),
        ("!0", 1),
        ("!5", 0),
    ],
)
def test_comparison_and_logical_operators(expression, expected):
    assert evaluate(expression) == expected


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("1 ? 10 : 20", 10),
        ("0 ? 10 : 20", 20),
        ("1 ? 0 ? 1 : 2 : 3", 2),
    ],
)
def test_ternary(expression, expected):
    assert evaluate(expression) == expected


def test_parameter_reference_is_resolved_and_evaluated():
    result = evaluate("WIDTH * 2", resolve_parameter=lambda name: "8" if name == "WIDTH" else "")
    assert result == 16


def test_parameter_reference_resolves_recursively():
    values = {"A": "B + 1", "B": "10"}
    result = evaluate("A * 2", resolve_parameter=values.get)
    assert result == 22


def test_circular_parameter_reference_raises_instead_of_recursing_forever():
    values = {"A": "B", "B": "A"}
    with pytest.raises(ExpressionError, match="circular parameter reference"):
        evaluate("A", resolve_parameter=values.get)


def test_resolver_exceptions_are_wrapped_clearly():
    def resolve(name: str) -> str:
        raise KeyError(name)

    with pytest.raises(ExpressionError, match="could not resolve parameter 'UNKNOWN'"):
        evaluate("UNKNOWN", resolve_parameter=resolve)


def test_identifier_without_a_resolver_raises():
    with pytest.raises(ExpressionError, match="no parameter resolver was given"):
        evaluate("WIDTH")


def test_parameter_resolver_builds_a_callback_from_a_parameter_list():
    parameters = [
        ipxact.Parameter(name="width", value="8", parameter_id="WIDTH"),
        ipxact.Parameter(name="unnamed", value="99"),  # no parameterId: not resolvable by name
    ]
    resolve = parameter_resolver(parameters)

    assert evaluate("WIDTH * 4", resolve_parameter=resolve) == 32
    with pytest.raises(ExpressionError, match="no parameter"):
        evaluate("unnamed", resolve_parameter=resolve)


@pytest.mark.parametrize(
    "expression",
    [
        "1 +",
        "(1 + 2",
        "1 2",
        "@",
        "8'zFF",  # unsupported base marker
    ],
)
def test_malformed_expressions_raise(expression):
    with pytest.raises(ExpressionError):
        evaluate(expression)
