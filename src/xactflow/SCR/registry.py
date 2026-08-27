from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator, List

from ..diagnostics import Diagnostic


@dataclass(frozen=True)
class Rule:
    """One IEEE 1685-2022 Annex B semantic consistency rule (SCR)."""

    id: str
    table: str
    name: str
    single_doc_check: bool
    post_config: bool
    description: str
    check: Callable[[object], Iterator[Diagnostic]]
    implemented: bool


_REGISTRY: List[Rule] = []


def rule(
    *,
    id: str,
    table: str,
    name: str,
    single_doc_check: bool,
    post_config: bool,
    description: str,
) -> Callable[[Callable[[object], Iterator[Diagnostic]]], Callable[[object], Iterator[Diagnostic]]]:
    """Decorator registering a check function as one working Annex B SCR rule."""

    def decorator(
        check: Callable[[object], Iterator[Diagnostic]]
    ) -> Callable[[object], Iterator[Diagnostic]]:
        _REGISTRY.append(
            Rule(
                id=id,
                table=table,
                name=name,
                single_doc_check=single_doc_check,
                post_config=post_config,
                description=description,
                check=check,
                implemented=True,
            )
        )
        return check

    return decorator


def _not_yet_implemented(_subject: object) -> Iterator[Diagnostic]:
    return []


def stub(
    *,
    id: str,
    table: str,
    name: str,
    single_doc_check: bool,
    post_config: bool,
    description: str,
) -> None:
    """Register an Annex B rule that is tracked (discoverable via all_rules()) but has no check
    logic implemented yet. Its check always reports nothing; `implemented` is False so callers
    can tell it apart from a working rule registered through @rule.
    """
    _REGISTRY.append(
        Rule(
            id=id,
            table=table,
            name=name,
            single_doc_check=single_doc_check,
            post_config=post_config,
            description=description,
            check=_not_yet_implemented,
            implemented=False,
        )
    )


def all_rules() -> List[Rule]:
    return list(_REGISTRY)
