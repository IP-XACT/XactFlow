import ipxact
import pytest

from xactflow.expressions import ExpressionError, evaluate, parameter_resolver


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("42", 42),
        ("0", 0),
        ("1_000", 1000),
        ("'h1f", 31),
        ("16'h00FF", 255),
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
        ("4'hFF", 15),
        ("8'd300", 44),
        ("16'hFFFF_FFFF", 65535),
        ("4'sh1F", -1),  # truncated to 4'hF first, then signed
    ],
)
def test_sized_literals_are_truncated_to_their_width(expression, expected):
    assert evaluate(expression) == expected


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("2+3*4", 14),
        ("(2+3)*4", 20),
        ("2**3**2", 64),  # left-associative: (2**3)**2
        ("-2**2", 4),  # unary binds tighter than ** in SystemVerilog, unlike Python
        ("2-3-4", -5),  # left-associative
    ],
)
def test_arithmetic_precedence_and_associativity(expression, expected):
    assert evaluate(expression) == expected


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("2**-1", 0),
        ("1**-3", 1),
        ("(-1)**-3", -1),
        ("(-1)**-2", 1),
        ("2**0", 1),
        ("2.0**-1", 0.5),  # a real operand gives a real result
    ],
)
def test_integer_power_with_a_negative_exponent(expression, expected):
    assert evaluate(expression) == expected


@pytest.mark.parametrize("expression", ["0**-1", "0.0**-1", "(-8.0)**0.5"])
def test_undefined_power_raises(expression):
    with pytest.raises(ExpressionError):
        evaluate(expression)


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("$clog2(0)", 0),
        ("$clog2(1)", 0),
        ("$clog2(2)", 1),
        ("$clog2(5)", 3),
        ("$clog2(8)", 3),
        ("$clog2(9)", 4),
        ("$clog2(DEPTH) + 1", 5),
        ("$sqrt(16.0)", 4.0),
        ("$pow(2, 10)", 1024.0),
        ("$floor(-2.5)", -3.0),
        ("$ceil(2.2)", 3.0),
        ("$log10(1000.0)", 3.0),
        ("$hypot(3.0, 4.0)", 5.0),
    ],
)
def test_system_functions(expression, expected):
    assert evaluate(expression, resolve_parameter={"DEPTH": "16"}.__getitem__) == expected


@pytest.mark.parametrize(
    "expression, message",
    [
        ("$ipxact_index_value(0)", r"unsupported function \$ipxact_index_value"),
        ("$clog2(1, 2)", r"\$clog2 takes 1 argument\(s\), got 2"),
        ("$clog2(-1)", "non-negative integer"),
        ("$clog2(2.5)", "non-negative integer"),
        ("$sqrt(-1.0)", r"\$sqrt\(-1.0\): math domain error"),
        ("$clog2", "expected '\\('"),
    ],
)
def test_system_function_errors(expression, message):
    with pytest.raises(ExpressionError, match=message):
        evaluate(expression)


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
        ("'hF0 & 'h0F", 0),
        ("'hF0 | 'h0F", 255),
        ("'hFF ^ 'h0F", 0xF0),
        ("5 & 3", 1),
        ("1 << 4", 16),
        ("256 >> 4", 16),
        ("~0 & 'hFF", 255),
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


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("N == 0 ? 0 : 32 / N", 0),
        ("N != 0 ? 32 / N : 0", 0),
        ("N != 0 && 32 / N > 4", 0),
        ("N == 0 || 32 / N > 4", 1),
        ("N != 0 && 1 / N && 2 / N", 0),
        ("N != 0 ? (N == 1 ? 1 / N : 2 / N) : 7", 7),
        ("N != 0 && UNKNOWN", 0),  # the skipped side is not resolved either
    ],
)
def test_only_the_selected_side_is_evaluated(expression, expected):
    resolve = {"N": "0"}.__getitem__
    assert evaluate(expression, resolve_parameter=resolve) == expected


@pytest.mark.parametrize("expression", ["1 ? 2 : (3", "0 && (1 +", "1 || 1 2"])
def test_the_skipped_side_is_still_checked_for_syntax(expression):
    with pytest.raises(ExpressionError):
        evaluate(expression)


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
        ipxact.Parameter(name="width", value=ipxact.Expression("8"), parameter_id="WIDTH"),
        # no parameterId: not resolvable by name
        ipxact.Parameter(name="unnamed", value=ipxact.Expression("99")),
    ]
    resolve = parameter_resolver(parameters)

    assert evaluate("WIDTH * 4", resolve_parameter=resolve) == 32
    with pytest.raises(ExpressionError, match="no parameter"):
        evaluate("unnamed", resolve_parameter=resolve)


def test_expression_object_is_evaluated_from_its_value():
    assert evaluate(ipxact.Expression("WIDTH - 1"), resolve_parameter=lambda name: "8") == 7


def test_expression_within_its_bounds_is_returned():
    assert evaluate(ipxact.Expression("4 * 2", minimum="8", maximum="8")) == 8


@pytest.mark.parametrize(
    "expression, message",
    [
        (ipxact.Expression("2 + 1", minimum="4"), "below its minimum 4"),
        (ipxact.Expression("2 * 8", maximum="15"), "above its maximum 15"),
        (ipxact.Expression("1", minimum="one"), "invalid minimum 'one'"),
    ],
)
def test_expression_out_of_its_bounds_raises(expression, message):
    with pytest.raises(ExpressionError, match=message):
        evaluate(expression)


def test_out_of_bounds_error_names_the_expression():
    with pytest.raises(ExpressionError, match=r"^register 'ctrl' size \('2 \* 8'\) evaluates to 16"):
        evaluate(ipxact.Expression("2 * 8", maximum="15"), name="register 'ctrl' size")


def _bounded_parameter(value, minimum=None, maximum=None, type="int", vectors=()):
    return ipxact.Parameter(
        name="width",
        value=ipxact.Expression(value),
        parameter_id="WIDTH",
        minimum=minimum,
        maximum=maximum,
        type=type,
        vectors=list(vectors),
    )


def _vector(left, right):
    return ipxact.Vector(left=ipxact.Expression(str(left)), right=ipxact.Expression(str(right)))


def test_parameter_within_its_bounds_is_resolved():
    resolve = parameter_resolver([_bounded_parameter("8", minimum="1", maximum="32")])
    assert evaluate("WIDTH * 2", resolve_parameter=resolve) == 16


@pytest.mark.parametrize(
    "parameter, message",
    [
        (_bounded_parameter("0", minimum="1"), r"parameter 'WIDTH' \('0'\) evaluates to 0, below its minimum 1"),
        (_bounded_parameter("64", maximum="32"), r"parameter 'WIDTH' \('64'\) evaluates to 64, above its maximum 32"),
        (_bounded_parameter("2.5", maximum="2.0", type="real"), r"above its maximum 2.0"),
    ],
)
def test_parameter_out_of_its_bounds_raises_naming_it(parameter, message):
    with pytest.raises(ExpressionError, match=message):
        evaluate("WIDTH * 2", resolve_parameter=parameter_resolver([parameter]))


@pytest.mark.parametrize("type", ["bit", "string"])
def test_bounds_of_a_bit_or_string_parameter_are_not_checked(type):
    # IEEE 1685-2022 C.6.2: minimum/maximum only apply to byte/shortint/int/longint/shortreal/real.
    vectors = [_vector(7, 0)] if type == "bit" else []
    resolve = parameter_resolver([_bounded_parameter("64", maximum="32", type=type, vectors=vectors)])
    assert evaluate("WIDTH", resolve_parameter=resolve) == 64


def test_identifier_may_contain_a_dollar_sign():
    assert evaluate("a$b + 1", resolve_parameter={"a$b": "1"}.__getitem__) == 2


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


def _typed(value, type, sign=None, vectors=(), parameter_id="P", **kwargs):
    return ipxact.Parameter(
        name=parameter_id.lower(),
        value=ipxact.Expression(value),
        parameter_id=parameter_id,
        type=type,
        sign=sign,
        vectors=list(vectors),
        **kwargs,
    )


@pytest.mark.parametrize(
    "parameter, expected",
    [
        (_typed("200", "byte"), -56),
        (_typed("200", "byte", sign="unsigned"), 200),
        (_typed("'hFFFFFFFF", "int"), -1),
        (_typed("2**40", "longint"), 2**40),
        (_typed("300", "bit", vectors=[_vector(7, 0)]), 44),
        (_typed("'hF", "bit", sign="signed", vectors=[_vector(3, 0)]), -1),
        (_typed("3", "bit"), 1),  # no vector: a single bit
        (_typed("2.6", "int"), 3),  # a real converts to an integer by rounding
        (_typed("-2.5", "int"), -3),  # ties away from zero
        (_typed("3", "real"), 3.0),
        (_typed("0.1", "shortreal"), 0.10000000149011612),
        (_typed("300", "string"), 300),  # the default type: not cast
    ],
)
def test_a_parameter_is_cast_to_its_type(parameter, expected):
    # IEEE 1685-2022 E.3.2/C.7 (implicit cast to the type), E.3.3 (sign).
    assert evaluate("P", resolve_parameter=parameter_resolver([parameter])) == expected
    assert evaluate(parameter) == expected


def test_parameter_bounds_are_checked_after_the_cast():
    parameter = _typed("200", "byte", minimum="0")
    with pytest.raises(ExpressionError, match=r"parameter 'P' \('200'\) evaluates to -56, below its minimum 0"):
        evaluate("P", resolve_parameter=parameter_resolver([parameter]))


def test_a_vector_bound_can_reference_a_parameter():
    width = _typed("4", "int", parameter_id="W")
    data = _typed("'hFF", "bit", vectors=[ipxact.Vector(left=ipxact.Expression("W - 1"), right=ipxact.Expression("0"))])
    assert evaluate("P", resolve_parameter=parameter_resolver([width, data])) == 15


def test_a_duplicate_parameter_id_raises_when_referenced():
    resolve = parameter_resolver([_typed("8", "int", parameter_id="W"), _typed("16", "int", parameter_id="W")])
    with pytest.raises(ExpressionError, match="parameterId 'W' is used by 2 parameters"):
        evaluate("W", resolve_parameter=resolve)


def test_an_array_parameter_raises():
    parameter = _typed("'{1, 2}", "int", arrays=[ipxact.ArrayBound(left=ipxact.Expression("0"), right=ipxact.Expression("1"))])
    with pytest.raises(ExpressionError, match="array parameters are not supported"):
        evaluate(parameter)


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("longint'(2**40)", 2**40),
        ("int'(1.6)", 2),
        ("int'(-2.5)", -3),
        ("byte'(200)", -56),
        ("bit'(3)", 1),
        ("8'(300)", 44),
        ("4'(300)", -4),  # a width cast keeps the operand's sign
        ("(2+2)'(300)", -4),
        ("W'(300)", -4),
        ("signed'(4'hF)", -1),
        ("unsigned'(-1)", 4294967295),
        ("real'(3)", 3.0),
        ("shortreal'(0.1)", 0.10000000149011612),
    ],
)
def test_casts(expression, expected):
    assert evaluate(expression, resolve_parameter={"W": "4"}.__getitem__) == expected


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("&4'b1111", 1),
        ("&4'b1101", 0),
        ("~&4'b1111", 0),
        ("|4'b0000", 0),
        ("~|4'b0000", 1),
        ("^3'b101", 0),
        ("^3'b100", 1),
        ("~^3'b100", 0),
        ("^~3'b101", 1),
        ("&'hFFFFFFFF", 1),  # unsized: 32 bits
        ("~4'h0", 15),  # unsigned: stays within its width
        ("~0", -1),
        ("-8 >> 1", 2147483644),  # logical shift
        ("-8 >>> 1", -4),
        ("1 -> 0", 0),
        ("0 -> 0 -> 0", 1),  # right-associative
        ("1 <-> 1", 1),
        ("1 <-> 0", 0),
        ("1 || 0 -> 0", 0),  # looser than ||
        ("1 ? 0 : 1 -> 0", 0),  # tighter than ?:
        ("3 inside {1, 3}", 1),
        ("3 inside {[1:2], 5}", 0),
        ("2 inside {[1:2], 5}", 1),
        ("1 + 2 inside {3}", 1),
    ],
)
def test_reduction_implication_and_inside_operators(expression, expected):
    assert evaluate(expression) == expected


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("{4'hA, 4'h5}", 165),
        ("{3{1'b1}}", 7),
        ("{2{4'hA}}", 170),
        ("{2{4'hA, 1'b0}}", 0b1010010100),
        ("(('h01FF) >> 0) & {3{1'b1}}", 7),  # from the Accellera Leon2 example
        ("{8'hA5}[3:0]", 5),
        ("{>>{8'hA5}}", 165),
        ("{<<{4'b0001}}", 0b1000),
        ("{<<4{16'hABCD}}", 0xDCBA),
        ("{<<byte{16'hABCD}}", 0xCDAB),
        ("{<<4{6'b110101}}", 0b010111),  # slices are taken from the right
        ("8'h0F & '1", 15),
        ("'0", 0),
    ],
)
def test_concatenation_replication_and_streaming(expression, expected):
    assert evaluate(expression) == expected


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("DV[7:4]", 0xA),
        ("DV[0]", 1),
        ("DV[0 +: 4]", 5),
        ("DV[7 -: 2]", 2),
        ("AV[0]", 1),  # [0:7]: index 0 is the most significant bit
        ("AV[0:1]", 3),
        ("AV[0 +: 3]", 6),
        ("AV[2 -: 3]", 6),
        ("I[31]", 1),
        ("\\a.b + 1", 2),  # escaped identifier (E.3.7.1)
        ("\\DV [1:0]", 1),
    ],
)
def test_bit_and_part_selects(expression, expected):
    resolve = parameter_resolver(
        [
            _typed("8'hA5", "bit", vectors=[_vector(7, 0)], parameter_id="DV"),
            _typed("8'b1100_0000", "bit", vectors=[_vector(0, 7)], parameter_id="AV"),
            _typed("-1", "int", parameter_id="I"),
            _typed("1", "int", parameter_id="a.b"),
        ]
    )
    assert evaluate(expression, resolve_parameter=resolve) == expected


@pytest.mark.parametrize(
    "expression, message",
    [
        ("{4'hA, 5}", "unsized value 5 in a concatenation"),
        ("{0{1'b1}}", "replication count must be positive"),
        ("{1.5, 4'hA}", "requires an integer operand"),
        ("DV[8]", r"index 8 is out of the range \[7:0\]"),
        ("DV[0:3]", r"part select \[0:3\] is reversed"),
        ("MV[0]", "multi-dimensional"),
        ("0x1F", "unexpected trailing token 'x1F'"),  # not IEEE 1800 number syntax
        ('"abc" == "abc"', "string expressions are not supported"),
        ("int + 1", "unexpected keyword 'int'"),
        ("0'(1)", "cast width must be positive"),
    ],
)
def test_width_dependent_errors(expression, message):
    resolve = parameter_resolver(
        [
            _typed("8'hA5", "bit", vectors=[_vector(7, 0)], parameter_id="DV"),
            _typed("0", "bit", vectors=[_vector(1, 0), _vector(3, 0)], parameter_id="MV"),
        ]
    )
    with pytest.raises(ExpressionError, match=message):
        evaluate(expression, resolve_parameter=resolve)


def test_the_skipped_side_is_not_checked_for_widths():
    assert evaluate("N != 0 ? {N{1'b1}} : 0", resolve_parameter={"N": "0"}.__getitem__) == 0
