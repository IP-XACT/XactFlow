"""Evaluates IEEE 1685-2022 IP-XACT expressions.

ipxact-compiler leaves expression fields (addressOffset, size, width, parameter values, ...)
unevaluated. This module computes their value, following the IP-XACT expression language of
IEEE 1685-2022 Annex E, a subset of IEEE 1800 SystemVerilog.

Supported: integral and real values, the operators of Table E.2 except the string ones, casts,
concatenation, replication, streaming, selects, and the math functions of E.5.1/E.5.2. A
referenced parameter is cast to its type and sign (E.3.2, E.3.3).
Not supported, because evaluate() returns one number:
- strings and $sformatf, whose result is text;
- array parameters, whose value is a list ('{1, 2, 3});
- the $ipxact_* functions, whose result is "unresolved" (E.2.10): it depends on a port value,
  a mode or an array index that only a design environment or a generator knows.

Simplification: each value keeps its own bit width and sign, but arithmetic does not follow
SystemVerilog's context-dependent width and sign rules (IEEE 1800 11.6, 11.8). It works on the
plain mathematical value, so 4'hF + 4'h1 is 16 and -1 < 'h1 is true.
"""

from __future__ import annotations

import math
import re
import struct
from dataclasses import dataclass, replace
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

import ipxact

Number = Union[int, float]
ResolvedParameter = Union[str, "ipxact.Expression", "ipxact.Parameter"]


class ExpressionError(Exception):
    """Raised when an expression cannot be tokenized, parsed, or evaluated."""


_TOKEN_SPEC = [
    ("SIZED", r"\d+'[sS]?[hHbBoOdD][0-9a-fA-F_]+"),
    ("UNSIZED", r"'[sS]?[hHbBoOdD][0-9a-fA-F_]+"),
    ("UNBASED", r"'[01]"),
    ("CAST", r"'\("),
    ("REAL", r"\d[\d_]*\.\d[\d_]*(?:[eE][+-]?\d+)?|\d[\d_]*[eE][+-]?\d+"),
    ("INT", r"\d[\d_]*"),
    ("IDENT", r"[A-Za-z_][A-Za-z0-9_$]*"),
    ("ESCAPED", r"\\\S+"),
    ("SYSFUNC", r"\$[A-Za-z_][A-Za-z0-9_$]*"),
    (
        "OP",
        r"<->|->|\*\*|<<<|>>>|<<|>>|<=|>=|==|!=|&&|\|\||\^~|~\^|~&|~\||\+:|-:"
        r"|[-+*/%&^|~!<>?:(),{}\[\]]",
    ),
    ("SKIP", r"[ \t\r\n]+"),
]
_TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in _TOKEN_SPEC))

# Loosest to tightest, excluding ->/<-> and ?: (looser than all of these) and unary/power/
# primary (tighter than all of these). Matches IEEE 1800's operator precedence table.
_PRECEDENCE = [
    ("||",),
    ("&&",),
    ("|",),
    ("^", "^~", "~^"),
    ("&",),
    ("==", "!="),
    ("<", "<=", ">", ">="),
    ("<<", ">>", "<<<", ">>>"),
    ("+", "-"),
    ("*", "/", "%"),
]
_RELATIONAL_LEVEL = 6

_UNARY_OPERATORS = ("+", "-", "!", "~", "&", "~&", "|", "~|", "^", "~^", "^~")
_LOGICAL_RESULT_OPERATORS = {"==", "!=", "<", "<=", ">", ">=", "&&", "||"}
_BITWISE_OPERATORS = {"&", "|", "^", "^~", "~^"}
_SHIFT_OPERATORS = {"<<", ">>", "<<<", ">>>"}

# Data types of Table E.1 that have a fixed width, and the keywords of E.3.7.2.
_INTEGER_TYPE_WIDTHS = {"byte": 8, "shortint": 16, "int": 32, "longint": 64}
_KEYWORDS = {"bit", "byte", "shortint", "int", "longint", "shortreal", "real", "signed", "unsigned", "inside", "with"}
_UNSIZED_WIDTH = 32  # IEEE 1800 5.7.1: an unsized number is (at least) 32 bits


@dataclass(frozen=True)
class _Value:
    """A value, with what casts, concatenation and selects need to know about its bits."""

    number: Number
    width: Optional[int] = None  # None: unsized (unsized literal, untyped parameter) or real
    signed: bool = True
    bounds: Optional[Tuple[int, int]] = None  # declared [left:right], for selects; default [width-1:0]
    packed_dimensions: int = 1
    fill: bool = False  # '1: all ones at the width of its context


_ZERO = _Value(0)


def _mask(width: int) -> int:
    return (1 << width) - 1


def _bit(condition: object) -> _Value:
    return _Value(1 if condition else 0, 1, False)


def _round(number: float) -> int:
    # IEEE 1800 6.12.2: a real converts to an integer by rounding, ties away from zero.
    return int(math.floor(abs(number) + 0.5)) * (1 if number >= 0 else -1)


def _resize(value: _Value, width: int, signed: bool, bounds: Optional[Tuple[int, int]] = None) -> _Value:
    """Cast an integral value to `width` bits (IEEE 1800 6.24): truncate or extend, then sign."""
    number = value.number
    if isinstance(number, float):
        if math.isinf(number) or math.isnan(number):
            raise ExpressionError(f"cannot convert {number} to an integer")
        number = _round(number)
    if value.fill:
        number = -1
    number &= _mask(width)
    if signed and number >> (width - 1):
        number -= 1 << width
    return _Value(number, width, signed, bounds)


def _to_shortreal(number: Number) -> float:
    try:
        return struct.unpack("f", struct.pack("f", float(number)))[0]
    except (OverflowError, struct.error) as exc:
        raise ExpressionError(f"{number} does not fit in a shortreal: {exc}") from None


def _fill_to(value: _Value, other: _Value) -> _Value:
    # '1 takes the width of the other operand (IEEE 1800 5.7.1); 32 bits next to an unsized one.
    if value.fill and not other.fill and not isinstance(other.number, float):
        return _resize(value, other.width or _UNSIZED_WIDTH, False)
    return value


def _require_int(value: _Value, what: str) -> int:
    if isinstance(value.number, float):
        raise ExpressionError(f"{what} requires an integer operand, got {value.number!r}")
    return value.number


def _bits(value: _Value, what: str) -> Tuple[int, int]:
    """The two's complement bit pattern of an integral value, and its width."""
    number = _require_int(value, what)
    width = value.width or _UNSIZED_WIDTH
    return number & _mask(width), width


def _concatenate(items: List[_Value]) -> _Value:
    number = width = 0
    for item in items:
        _require_int(item, "a concatenation")
        if item.width is None:
            # IEEE 1800 11.4.12: an unsized constant is not allowed in a concatenation.
            raise ExpressionError(f"unsized value {item.number} in a concatenation")
        number = (number << item.width) | (item.number & _mask(item.width))
        width += item.width
    return _Value(number, width, False)


def _parse_sized_literal(text: str) -> _Value:
    # e.g. "8'hFF" (sized), "'h1F" (unsized, 32-bit per IEEE 1800), "4'shA" (sized, signed).
    size_str, rest = text.split("'", 1)
    signed = rest[0] in "sS"
    if signed:
        rest = rest[1:]
    base_char = rest[0].lower()
    digits = rest[1:].replace("_", "")
    base = {"h": 16, "b": 2, "o": 8, "d": 10}[base_char]
    try:
        value = int(digits, base)
    except ValueError:
        raise ExpressionError(f"invalid digits {digits!r} for base {base_char!r} in {text!r}") from None
    width = int(size_str) if size_str else _UNSIZED_WIDTH
    if width == 0:
        raise ExpressionError(f"a sized literal cannot have a width of 0: {text!r}")
    if size_str:
        # IEEE 1800 5.7.1: a value wider than its declared size is truncated from the left.
        value &= _mask(width)
    if signed and value >= (1 << (width - 1)):
        value -= 1 << width
    return _Value(value, width if size_str else None, signed)


def _clog2(value: Number) -> int:
    # IEEE 1800 20.8.1: ceil(log2(value)), and 0 for an argument of 0 or 1.
    if isinstance(value, float) or value < 0:
        raise ExpressionError(f"$clog2 requires a non-negative integer argument, got {value!r}")
    return (value - 1).bit_length() if value > 1 else 0


# System function name -> (number of arguments, implementation). The real math functions are
# E.5.2 (IEEE 1800 20.8.2); they always return a real, like in SystemVerilog.
_SYSTEM_FUNCTIONS = {
    "$clog2": (1, _clog2),
    "$ln": (1, math.log),
    "$log10": (1, math.log10),
    "$exp": (1, math.exp),
    "$sqrt": (1, math.sqrt),
    "$pow": (2, math.pow),
    "$floor": (1, lambda x: float(math.floor(x))),
    "$ceil": (1, lambda x: float(math.ceil(x))),
    "$sin": (1, math.sin),
    "$cos": (1, math.cos),
    "$tan": (1, math.tan),
    "$asin": (1, math.asin),
    "$acos": (1, math.acos),
    "$atan": (1, math.atan),
    "$atan2": (2, math.atan2),
    "$hypot": (2, math.hypot),
    "$sinh": (1, math.sinh),
    "$cosh": (1, math.cosh),
    "$tanh": (1, math.tanh),
    "$asinh": (1, math.asinh),
    "$acosh": (1, math.acosh),
    "$atanh": (1, math.atanh),
}


class _Token:
    __slots__ = ("kind", "text", "pos")

    def __init__(self, kind: str, text: str, pos: int) -> None:
        self.kind = kind
        self.text = text
        self.pos = pos


def _tokenize(expression: str) -> List[_Token]:
    tokens: List[_Token] = []
    pos = 0
    while pos < len(expression):
        if expression[pos] == '"':
            raise ExpressionError(f"string expressions are not supported: {expression!r}")
        match = _TOKEN_RE.match(expression, pos)
        if match is None:
            raise ExpressionError(
                f"unexpected character {expression[pos]!r} at position {pos} in {expression!r}"
            )
        kind = match.lastgroup
        text = match.group()
        if kind != "SKIP":
            tokens.append(_Token(kind, text, pos))
        pos = match.end()
    tokens.append(_Token("EOF", "", len(expression)))
    return tokens


class _Parser:
    def __init__(
        self,
        tokens: List[_Token],
        resolve_parameter: Optional[Callable[[str], ResolvedParameter]],
        resolving: Set[str],
    ) -> None:
        self._tokens = tokens
        self._pos = 0
        self._resolve_parameter = resolve_parameter
        self._resolving = resolving
        # > 0 while parsing a ?: branch or &&/|| operand that is not selected: it is parsed for
        # syntax but not evaluated (IEEE 1800 11.4.7, 11.4.11), every value in it is 0.
        self._skipping = 0

    def _skipped(self, parse: Callable[[], _Value]) -> _Value:
        self._skipping += 1
        try:
            parse()
        finally:
            self._skipping -= 1
        return _ZERO

    def _peek(self) -> _Token:
        return self._tokens[self._pos]

    def _advance(self) -> _Token:
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    def _expect(self, text: str) -> None:
        token = self._advance()
        if token.text != text:
            raise ExpressionError(f"expected {text!r}, got {token.text!r}")

    def parse(self) -> _Value:
        value = self._ternary()
        if self._peek().kind != "EOF":
            raise ExpressionError(f"unexpected trailing token {self._peek().text!r}")
        return value

    def _ternary(self) -> _Value:
        condition = self._implication()
        if self._peek().text == "?":
            self._advance()
            then_value = self._ternary() if condition.number else self._skipped(self._ternary)
            self._expect(":")
            else_value = self._skipped(self._ternary) if condition.number else self._ternary()
            return then_value if condition.number else else_value
        return condition

    def _implication(self) -> _Value:
        # -> and <-> bind looser than || and tighter than ?:, right-associative; both operands
        # are always evaluated (IEEE 1800 11.4.7).
        left = self._binary(0)
        if self._peek().text in ("->", "<->"):
            op = self._advance().text
            right = self._implication()
            if self._skipping:
                return _ZERO
            if op == "->":
                return _bit(not left.number or right.number)
            return _bit(bool(left.number) == bool(right.number))
        return left

    def _binary(self, level: int) -> _Value:
        if level >= len(_PRECEDENCE):
            return self._power()
        left = self._binary(level + 1)
        while True:
            token = self._peek()
            if level == _RELATIONAL_LEVEL and token.kind == "IDENT" and token.text == "inside":
                self._advance()
                left = self._inside(left)
                continue
            if token.text not in _PRECEDENCE[level]:
                return left
            op = self._advance().text
            if (op == "&&" and not left.number) or (op == "||" and left.number):
                self._skipped(lambda: self._binary(level + 1))
                left = _bit(op == "||")
                continue
            right = self._binary(level + 1)
            left = self._binary_operation(op, left, right)

    def _binary_operation(self, op: str, left: _Value, right: _Value) -> _Value:
        if self._skipping:
            return _ZERO
        if op not in _SHIFT_OPERATORS and op not in ("&&", "||"):
            left, right = _fill_to(left, right), _fill_to(right, left)
        left_number, right_number = left.number, right.number
        if op == ">>" and isinstance(left_number, int) and left_number < 0 and right_number:
            # A logical shift fills with 0, also on a negative (signed) value.
            left_number &= _mask(left.width or _UNSIZED_WIDTH)
        number = self._apply_binary(op, left_number, right_number)
        if op in _LOGICAL_RESULT_OPERATORS:
            return _bit(number)
        if isinstance(number, float):
            return _Value(number)
        if op in _SHIFT_OPERATORS:
            width, signed = left.width, left.signed
        else:
            width = max(left.width, right.width) if left.width and right.width else None
            signed = left.signed and right.signed
        if op in _BITWISE_OPERATORS and not signed:
            number &= _mask(width or _UNSIZED_WIDTH)
        return _Value(number, width, signed)

    def _inside(self, value: _Value) -> _Value:
        # IEEE 1800 11.4.13: `value inside { item, [low:high], ... }`.
        self._expect("{")
        found = False
        while True:
            if self._peek().text == "[":
                self._advance()
                low = self._ternary()
                self._expect(":")
                high = self._ternary()
                self._expect("]")
                found = found or (low.number <= value.number <= high.number)
            else:
                item = self._ternary()
                found = found or self._binary_operation("==", value, item).number == 1
            if self._peek().text != ",":
                break
            self._advance()
        self._expect("}")
        return _ZERO if self._skipping else _bit(found)

    def _power(self) -> _Value:
        # Left-associative like every IEEE 1800 binary operator (11.3.2): 2**3**2 is (2**3)**2.
        value = self._unary()
        while self._peek().text == "**":
            self._advance()
            exponent = self._unary()
            if not self._skipping:
                number = self._apply_power(value.number, exponent.number)
                value = _Value(number) if isinstance(number, float) else _Value(number, value.width, value.signed)
        return value

    @staticmethod
    def _apply_power(base: Number, exponent: Number) -> Number:
        if isinstance(base, int) and isinstance(exponent, int) and exponent < 0:
            # IEEE 1800 Table 11-4: an integer power with a negative exponent.
            if base == 0:
                raise ExpressionError(f"{base} ** {exponent} is undefined")
            if base == 1:
                return 1
            if base == -1:
                return 1 if exponent % 2 == 0 else -1
            return 0
        try:
            result = base**exponent
        except (ZeroDivisionError, OverflowError) as exc:
            raise ExpressionError(f"{base} ** {exponent}: {exc}") from None
        if isinstance(result, complex):
            raise ExpressionError(f"{base} ** {exponent} is not a real number")
        return result

    def _unary(self) -> _Value:
        token = self._peek()
        if token.text not in _UNARY_OPERATORS:
            return self._primary()
        self._advance()
        operand = self._unary()
        if self._skipping:
            return _ZERO
        op = token.text
        if op == "+":
            return operand
        if op == "-":
            return replace(operand, number=-operand.number, bounds=None, fill=False)
        if op == "!":
            return _bit(not operand.number)
        if op == "~":
            number = ~_require_int(operand, "'~'")
            if not operand.signed:
                number &= _mask(operand.width or _UNSIZED_WIDTH)
            return _Value(number, operand.width, operand.signed)
        # Reduction operators (IEEE 1800 11.4.9) work on every bit of the operand.
        bits, width = _bits(operand, f"'{op}'")
        if op in ("&", "~&"):
            result = bits == _mask(width)
        elif op in ("|", "~|"):
            result = bits != 0
        else:
            result = bin(bits).count("1") % 2 == 1
        return _bit(result != (op in ("~&", "~|", "~^", "^~")))

    def _primary(self) -> _Value:
        value = self._primary_without_cast()
        while self._peek().kind == "CAST":
            # constant_primary ' ( expression ): a width cast (E.6.3.4, IEEE 1800 6.24.1).
            self._advance()
            operand = self._ternary()
            self._expect(")")
            if self._skipping:
                value = _ZERO
                continue
            width = _require_int(value, "a width cast")
            if width <= 0:
                raise ExpressionError(f"a cast width must be positive, got {width}")
            value = _resize(operand, width, operand.signed)
        return value

    def _primary_without_cast(self) -> _Value:
        token = self._advance()
        if token.kind == "INT":
            return _Value(int(token.text.replace("_", "")))
        if token.kind == "REAL":
            return _Value(float(token.text.replace("_", "")))
        if token.kind in ("SIZED", "UNSIZED"):
            return _parse_sized_literal(token.text)
        if token.kind == "UNBASED":
            return _Value(1, 1, False, fill=True) if token.text == "'1" else _Value(0, 1, False)
        if token.kind == "IDENT" and token.text in _KEYWORDS:
            if self._peek().kind == "CAST":
                return self._type_cast(token.text)
            raise ExpressionError(f"unexpected keyword {token.text!r}")
        if token.kind in ("IDENT", "ESCAPED"):
            name = token.text[1:] if token.kind == "ESCAPED" else token.text
            value = _ZERO if self._skipping else self._resolve_identifier(name)
            return self._select(value) if self._peek().text == "[" else value
        if token.kind == "SYSFUNC":
            return self._call_system_function(token.text)
        if token.text == "(":
            value = self._ternary()
            self._expect(")")
            return value
        if token.text == "{":
            value = self._concatenation()
            return self._select(value) if self._peek().text == "[" else value
        raise ExpressionError(f"unexpected token {token.text!r}")

    def _type_cast(self, keyword: str) -> _Value:
        # simple_type ' ( expression ) and signing ' ( expression ) (E.6.1, IEEE 1800 6.24.1).
        self._advance()
        operand = self._ternary()
        self._expect(")")
        if self._skipping:
            return _ZERO
        if keyword in _INTEGER_TYPE_WIDTHS:
            return _resize(operand, _INTEGER_TYPE_WIDTHS[keyword], True)
        if keyword == "bit":
            return _resize(operand, 1, False)
        if keyword == "real":
            return _Value(float(operand.number))
        if keyword == "shortreal":
            return _Value(_to_shortreal(operand.number))
        if keyword in ("signed", "unsigned"):
            _require_int(operand, f"a {keyword} cast")
            return _resize(operand, operand.width or _UNSIZED_WIDTH, keyword == "signed")
        raise ExpressionError(f"unexpected keyword {keyword!r}")

    def _concatenation(self) -> _Value:
        # After '{': a streaming expression, a replication {n{...}}, or a concatenation {a, b}.
        if self._peek().text in ("<<", ">>"):
            return self._streaming()
        first = self._ternary()
        if self._peek().text == "{":
            self._advance()
            items = self._concatenation_items()
            self._expect("}")
            self._expect("}")
            if self._skipping:
                return _ZERO
            count = _require_int(first, "a replication count")
            if count <= 0:
                raise ExpressionError(f"a replication count must be positive, got {count}")
            return _concatenate(items * count)
        items = [first]
        while self._peek().text == ",":
            self._advance()
            items.append(self._ternary())
        self._expect("}")
        return _ZERO if self._skipping else _concatenate(items)

    def _concatenation_items(self) -> List[_Value]:
        items = [self._ternary()]
        while self._peek().text == ",":
            self._advance()
            items.append(self._ternary())
        return items

    def _streaming(self) -> _Value:
        # { << slice_size { items } } (IEEE 1800 11.4.14). The result keeps the width of the
        # items, as in a self-determined context.
        op = self._advance().text
        slice_size = 1
        if self._peek().text != "{":
            token = self._peek()
            if token.kind == "IDENT" and token.text in _INTEGER_TYPE_WIDTHS:
                self._advance()
                slice_size = _INTEGER_TYPE_WIDTHS[token.text]
            else:
                slice_size = self._ternary().number
        self._expect("{")
        items = self._concatenation_items()
        self._expect("}")
        self._expect("}")
        if self._skipping:
            return _ZERO
        value = _concatenate(items)
        if op == ">>":
            return value
        if not isinstance(slice_size, int) or slice_size <= 0:
            raise ExpressionError(f"a stream slice size must be a positive integer, got {slice_size!r}")
        bits = format(value.number, f"0{value.width}b")
        # Slices are taken from the right, and the last one may be shorter.
        slices = [bits[max(0, end - slice_size) : end] for end in range(len(bits), 0, -slice_size)]
        return _Value(int("".join(slices), 2), value.width, False)

    def _select(self, value: _Value) -> _Value:
        # [index], [msb:lsb], [base+:width] or [base-:width] (E.6.3.4, IEEE 1800 11.5.1).
        self._expect("[")
        first = self._ternary()
        kind = None
        if self._peek().text in (":", "+:", "-:"):
            kind = self._advance().text
            second = self._ternary()
        self._expect("]")
        if self._skipping:
            return _ZERO
        if value.packed_dimensions > 1:
            raise ExpressionError("a select on a multi-dimensional bit vector is not supported")
        bits, width = _bits(value, "a bit select")
        left, right = value.bounds or (width - 1, 0)
        descending = left >= right
        index = _require_int(first, "a select index")
        if kind is None:
            msb_index = lsb_index = index
        elif kind == ":":
            msb_index, lsb_index = index, _require_int(second, "a select index")
            if (msb_index >= lsb_index) != descending and msb_index != lsb_index:
                raise ExpressionError(f"part select [{msb_index}:{lsb_index}] is reversed for [{left}:{right}]")
        else:
            count = _require_int(second, "a part select width")
            if count <= 0:
                raise ExpressionError(f"a part select width must be positive, got {count}")
            low, high = (index, index + count - 1) if kind == "+:" else (index - count + 1, index)
            msb_index, lsb_index = (high, low) if descending else (low, high)

        def position(i: int) -> int:
            if not min(left, right) <= i <= max(left, right):
                raise ExpressionError(f"index {i} is out of the range [{left}:{right}]")
            return i - right if descending else right - i

        low_position, high_position = position(lsb_index), position(msb_index)
        selected = high_position - low_position + 1
        return _Value((bits >> low_position) & _mask(selected), selected, False)

    def _call_system_function(self, name: str) -> _Value:
        if name not in _SYSTEM_FUNCTIONS:
            raise ExpressionError(f"unsupported function {name}")
        arity, function = _SYSTEM_FUNCTIONS[name]
        self._expect("(")
        args = [self._ternary()]
        while self._peek().text == ",":
            self._advance()
            args.append(self._ternary())
        self._expect(")")
        if len(args) != arity:
            raise ExpressionError(f"{name} takes {arity} argument(s), got {len(args)}")
        if self._skipping:
            return _ZERO
        numbers = [arg.number for arg in args]
        try:
            result = function(*numbers)
        except (ValueError, OverflowError) as exc:
            raise ExpressionError(f"{name}({', '.join(map(str, numbers))}): {exc}") from None
        return _Value(result) if isinstance(result, float) else _Value(result, 32, True)

    def _resolve_identifier(self, name: str) -> _Value:
        if self._resolve_parameter is None:
            raise ExpressionError(f"expression references '{name}' but no parameter resolver was given")
        if name in self._resolving:
            raise ExpressionError(f"circular parameter reference involving '{name}'")
        try:
            raw = self._resolve_parameter(name)
        except ExpressionError:
            raise
        except Exception as exc:
            raise ExpressionError(f"could not resolve parameter '{name}': {exc}") from exc
        self._resolving.add(name)
        try:
            return _evaluate(raw, self._resolve_parameter, f"parameter '{name}'", self._resolving)
        finally:
            self._resolving.discard(name)

    @staticmethod
    def _apply_binary(op: str, left: Number, right: Number) -> Number:
        if op == "||":
            return 1 if (left or right) else 0
        if op == "&&":
            return 1 if (left and right) else 0
        if op == "==":
            return int(left == right)
        if op == "!=":
            return int(left != right)
        if op in ("<", "<=", ">", ">="):
            if op == "<":
                return int(left < right)
            if op == "<=":
                return int(left <= right)
            if op == ">":
                return int(left > right)
            return int(left >= right)
        if op in _BITWISE_OPERATORS or op in _SHIFT_OPERATORS:
            for operand in (left, right):
                if isinstance(operand, float):
                    raise ExpressionError(f"'{op}' requires an integer operand, got {operand!r}")
            if op == "&":
                return left & right
            if op == "|":
                return left | right
            if op == "^":
                return left ^ right
            if op in ("^~", "~^"):
                return ~(left ^ right)
            if right < 0:
                raise ExpressionError(f"a shift amount cannot be negative, got {right}")
            if op in ("<<", "<<<"):
                return left << right
            return left >> right
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                raise ExpressionError("division by zero")
            if isinstance(left, int) and isinstance(right, int):
                # SV integer division truncates toward zero, unlike Python's floor division.
                quotient = abs(left) // abs(right)
                return -quotient if (left < 0) != (right < 0) else quotient
            return left / right
        if op == "%":
            if right == 0:
                raise ExpressionError("modulo by zero")
            if isinstance(left, int) and isinstance(right, int):
                remainder = abs(left) % abs(right)
                return -remainder if left < 0 else remainder
            return math.fmod(left, right)
        raise ExpressionError(f"unsupported operator {op!r}")


def evaluate(
    expression: Union[str, "ipxact.Expression", "ipxact.Parameter"],
    resolve_parameter: Optional[Callable[[str], ResolvedParameter]] = None,
    *,
    name: Optional[str] = None,
) -> Number:
    """Evaluate `expression` (text, an ipxact.Expression or an ipxact.Parameter) to an int or float.

    `resolve_parameter` maps a referenced parameterId to that parameter (or its expression),
    which is evaluated recursively. A parameter is cast to its type and sign, and checked
    against its minimum/maximum; an ipxact.Expression is checked against its own. `name`
    (e.g. "register 'ctrl' size") is used in the out-of-bounds error message.
    Any failure (unknown or circular reference, out of bounds, ...) raises ExpressionError.
    """
    return _evaluate(expression, resolve_parameter, name, set()).number


def _evaluate(
    expression: Union[str, "ipxact.Expression", "ipxact.Parameter"],
    resolve_parameter: Optional[Callable[[str], ResolvedParameter]],
    name: Optional[str],
    resolving: Set[str],
) -> _Value:
    if isinstance(expression, ipxact.Parameter):
        return _evaluate_parameter(expression, resolve_parameter, name, resolving)
    minimum = maximum = None
    if isinstance(expression, ipxact.Expression):
        minimum, maximum = expression.minimum, expression.maximum
        expression = expression.value
    value = _Parser(_tokenize(expression), resolve_parameter, resolving).parse()
    subject = f"{name} ({expression!r})" if name else repr(expression)
    _check_bounds(subject, value.number, minimum, maximum)
    return value


_BOUNDED_PARAMETER_TYPES = {"byte", "shortint", "int", "longint", "shortreal", "real"}


def _evaluate_parameter(
    parameter: "ipxact.Parameter",
    resolve_parameter: Optional[Callable[[str], ResolvedParameter]],
    name: Optional[str],
    resolving: Set[str],
) -> _Value:
    name = name or f"parameter '{parameter.parameter_id or parameter.name}'"
    if parameter.arrays:
        raise ExpressionError(f"{name}: array parameters are not supported")
    value = _evaluate(parameter.value, resolve_parameter, name, resolving)
    value = _cast_to_parameter_type(parameter, value, resolve_parameter, name, resolving)
    if parameter.type in _BOUNDED_PARAMETER_TYPES:
        # C.6.2: minimum/maximum only apply to these types, in the parameter's type and sign.
        _check_bounds(f"{name} ({parameter.value.value!r})", value.number, parameter.minimum, parameter.maximum)
    return value


def _cast_to_parameter_type(
    parameter: "ipxact.Parameter",
    value: _Value,
    resolve_parameter: Optional[Callable[[str], ResolvedParameter]],
    name: str,
    resolving: Set[str],
) -> _Value:
    # E.3.2, C.7: the value is implicitly cast to the parameter's type; E.3.3: `sign` changes
    # the default signed-ness of the integral types.
    kind = parameter.type
    if kind in _INTEGER_TYPE_WIDTHS:
        return _resize(value, _INTEGER_TYPE_WIDTHS[kind], parameter.sign != "unsigned")
    if kind == "bit":
        # 1 bit, unless vectors are given (C.6.2): their sizes multiply.
        sizes, bounds = [], None
        for vector in parameter.vectors:
            left = _evaluate(vector.left, resolve_parameter, f"{name} vector left", resolving).number
            right = _evaluate(vector.right, resolve_parameter, f"{name} vector right", resolving).number
            if not isinstance(left, int) or not isinstance(right, int):
                raise ExpressionError(f"{name}: vector bounds must be integers, got [{left}:{right}]")
            sizes.append(abs(left - right) + 1)
            bounds = (left, right)
        width = math.prod(sizes) if sizes else 1
        resized = _resize(value, width, parameter.sign == "signed", bounds if len(sizes) == 1 else None)
        return replace(resized, packed_dimensions=max(1, len(sizes)))
    if kind == "real":
        return _Value(float(value.number))
    if kind == "shortreal":
        return _Value(_to_shortreal(value.number))
    return value  # string (the default type): not cast


def _check_bounds(subject: str, value: Number, minimum: Optional[str], maximum: Optional[str]) -> None:
    if minimum is not None and value < _parse_bound(subject, "minimum", minimum):
        raise ExpressionError(f"{subject} evaluates to {value}, below its minimum {minimum}")
    if maximum is not None and value > _parse_bound(subject, "maximum", maximum):
        raise ExpressionError(f"{subject} evaluates to {value}, above its maximum {maximum}")


def _parse_bound(subject: str, which: str, bound: str) -> Number:
    # xs:int on an expression element (simpleTypes.xsd), but on a parameter it has the
    # parameter's own type, which may be real (commonStructures.xsd).
    try:
        return int(bound)
    except ValueError:
        pass
    try:
        return float(bound)
    except ValueError:
        raise ExpressionError(f"invalid {which} {bound!r} on {subject}") from None


def parameter_resolver(parameters: Iterable["ipxact.Parameter"]) -> Callable[[str], "ipxact.Parameter"]:
    """Build a resolve_parameter callback for evaluate() from a list of Parameters, keyed by
    parameterId; a Parameter without one cannot be referenced.

    Referencing an unknown parameterId, or one used by several parameters (E.3.6 requires it
    to be unique), raises ExpressionError.
    """
    by_id: Dict[str, List["ipxact.Parameter"]] = {}
    for parameter in parameters:
        if parameter.parameter_id is not None:
            by_id.setdefault(parameter.parameter_id, []).append(parameter)

    def resolve(name: str) -> "ipxact.Parameter":
        if name not in by_id:
            raise ExpressionError(f"no parameter with parameterId {name!r} is available")
        if len(by_id[name]) > 1:
            raise ExpressionError(f"parameterId {name!r} is used by {len(by_id[name])} parameters")
        return by_id[name][0]

    return resolve
