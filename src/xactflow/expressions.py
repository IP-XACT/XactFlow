"""Evaluates IEEE 1685-2022 IP-XACT expressions.

IP-XACT expression fields (addressOffset, size, range, width, bitOffset, parameter values,
...) hold raw, unevaluated strings, ipxact-compiler deliberately leaves them as such
(Expression = str, which defines each expression "type" purely as a result-type/range constraint).
This module is XactFlow's evaluator for that syntax: given an expression string, and
optionally a way to resolve a parameterId referenced within it, compute its concrete value.

Scope: integer and real (floating-point) arithmetic, matching what address/size/
width/offset expressions actually need. String expressions (ipxact:stringExpression and SV
string/concatenation syntax) and the IP-XACT-specific builtin functions ($ipxact_index_value(),
$ipxact_mode_condition(), etc., used in mode conditions and packet fields) are out of scope
for now, not implemented. Nothing in this module is wired into any SCR rule yet.

Also deliberately simplified: a sized literal (e.g. 8'hFF, 4'shA) is interpreted at its own
declared width and signedness, but arithmetic on top of that does not replicate SystemVerilog's
full context-dependent result-width/signedness propagation, and does not truncate or wrap
intermediate results to some inferred bit width; every value is treated as its plain
mathematical integer or real value once parsed. This matches how IP-XACT expressions are used
in practice, and keeps this a good-faith evaluator rather than a full SystemVerilog
constant-expression semantics implementation.
"""

from __future__ import annotations

import math
import re
from typing import Callable, Iterable, List, Optional, Set, Union

import ipxact

Number = Union[int, float]


class ExpressionError(Exception):
    """Raised when an expression cannot be tokenized, parsed, or evaluated."""


_TOKEN_SPEC = [
    ("SIZED", r"\d+'[sS]?[hHbBoOdD][0-9a-fA-F_]+"),
    ("UNSIZED", r"'[sS]?[hHbBoOdD][0-9a-fA-F_]+"),
    ("HEXC", r"0[xX][0-9a-fA-F_]+"),
    ("REAL", r"\d[\d_]*\.\d[\d_]*(?:[eE][+-]?\d+)?|\d[\d_]*[eE][+-]?\d+"),
    ("INT", r"\d[\d_]*"),
    ("IDENT", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("OP", r"\*\*|<<<|>>>|<<|>>|<=|>=|==|!=|&&|\|\||\^~|~\^|[-+*/%&^|~!<>?:()]"),
    ("SKIP", r"[ \t\r\n]+"),
]
_TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in _TOKEN_SPEC))

# Loosest to tightest, excluding ternary (handled separately, looser than all of these) and
# unary/power/primary (handled separately, tighter than all of these). Matches IEEE 1800's
# operator precedence table.
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


def _parse_sized_literal(text: str) -> int:
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
    if signed:
        width = int(size_str) if size_str else 32
        if value >= (1 << (width - 1)):
            value -= 1 << width
    return value


class _Parser:
    def __init__(
        self,
        tokens: List[_Token],
        resolve_parameter: Optional[Callable[[str], str]],
        resolving: Set[str],
    ) -> None:
        self._tokens = tokens
        self._pos = 0
        self._resolve_parameter = resolve_parameter
        self._resolving = resolving

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

    def parse(self) -> Number:
        value = self._ternary()
        if self._peek().kind != "EOF":
            raise ExpressionError(f"unexpected trailing token {self._peek().text!r}")
        return value

    def _ternary(self) -> Number:
        condition = self._binary(0)
        if self._peek().text == "?":
            self._advance()
            then_value = self._ternary()
            self._expect(":")
            else_value = self._ternary()
            return then_value if condition else else_value
        return condition

    def _binary(self, level: int) -> Number:
        if level >= len(_PRECEDENCE):
            return self._power()
        left = self._binary(level + 1)
        while self._peek().text in _PRECEDENCE[level]:
            op = self._advance().text
            right = self._binary(level + 1)
            left = self._apply_binary(op, left, right)
        return left

    def _power(self) -> Number:
        base = self._unary()
        if self._peek().text == "**":
            self._advance()
            exponent = self._power()  # right-associative
            return base**exponent
        return base

    def _unary(self) -> Number:
        token = self._peek()
        if token.text in ("+", "-", "!", "~"):
            self._advance()
            operand = self._unary()
            if token.text == "+":
                return operand
            if token.text == "-":
                return -operand
            if token.text == "!":
                return 0 if operand else 1
            self._require_int(operand, "~")
            return ~operand
        return self._primary()

    def _primary(self) -> Number:
        token = self._advance()
        if token.kind == "INT":
            return int(token.text.replace("_", ""))
        if token.kind == "REAL":
            return float(token.text.replace("_", ""))
        if token.kind == "HEXC":
            return int(token.text.replace("_", ""), 16)
        if token.kind in ("SIZED", "UNSIZED"):
            return _parse_sized_literal(token.text)
        if token.kind == "IDENT":
            return self._resolve_identifier(token.text)
        if token.text == "(":
            value = self._ternary()
            self._expect(")")
            return value
        raise ExpressionError(f"unexpected token {token.text!r}")

    def _resolve_identifier(self, name: str) -> Number:
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
            return evaluate(raw, self._resolve_parameter, _resolving=self._resolving)
        finally:
            self._resolving.discard(name)

    @staticmethod
    def _require_int(value: Number, op: str) -> None:
        if isinstance(value, float):
            raise ExpressionError(f"'{op}' requires an integer operand, got {value!r}")

    def _apply_binary(self, op: str, left: Number, right: Number) -> Number:
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
        if op in ("&", "|", "^", "^~", "~^", "<<", ">>", "<<<", ">>>"):
            self._require_int(left, op)
            self._require_int(right, op)
            if op == "&":
                return left & right
            if op == "|":
                return left | right
            if op == "^":
                return left ^ right
            if op in ("^~", "~^"):
                return ~(left ^ right)
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
    expression: str,
    resolve_parameter: Optional[Callable[[str], str]] = None,
    *,
    _resolving: Optional[Set[str]] = None,
) -> Number:
    """Evaluate `expression` to a concrete int or float.

    `resolve_parameter`, if given, maps a parameterId referenced by name in the expression to
    that parameter's own (unevaluated) Expression string, which is evaluated recursively; an
    identifier with no resolver given, or one `resolve_parameter` does not recognize, raises
    ExpressionError. A circular chain of parameter references raises ExpressionError instead of
    recursing forever.
    """
    tokens = _tokenize(expression)
    parser = _Parser(tokens, resolve_parameter, _resolving if _resolving is not None else set())
    return parser.parse()


def parameter_resolver(parameters: Iterable["ipxact.Parameter"]) -> Callable[[str], str]:
    """Build a resolve_parameter callback for evaluate() from a Component's/Design's own
    Parameter list, keyed by parameterId.

    A Parameter with no parameterId set is not resolvable by name from an expression (matches
    Annex C.6.2: parameterId is only required when the parameter's resolve is user/generated,
    or it is referenced from an expression, so a plain immediate-value parameter may not have
    one at all).
    """
    by_id = {p.parameter_id: p.value for p in parameters if p.parameter_id is not None}

    def resolve(name: str) -> str:
        if name not in by_id:
            raise ExpressionError(f"no parameter with parameterId {name!r} is available")
        return by_id[name]

    return resolve
