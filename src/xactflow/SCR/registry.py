from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator, List

from ..diagnostics import Diagnostic


@dataclass(frozen=True)
class Rule:
    """One IEEE 1685-2022 Annex B semantic consistency rule (SCR).

    single_doc_check and post_config mirror Annex B's own two columns (see B.2): single_doc_check
    is True when the rule can be checked by examining one IP-XACT document alone, no cross-file
    resolution needed; False when it requires the relationships between documents. post_config is
    True when the rule only applies once configuration (DesignConfiguration-driven overrides) has
    been completed. It is carried here for fidelity with Annex B, but XactFlow does not yet have a
    separate configuration-application stage, so it does not currently affect when a rule runs;
    single_doc_check alone decides whether scr.runner dispatches a rule to
    run_single_doc_checks (check takes one parsed document) or run_post_config_checks (check
    takes an elaborate.ElaboratedDesign).
    """

    id: str
    table: str
    name: str
    single_doc_check: bool
    post_config: bool
    description: str
    check: Callable[[object], Iterator[Diagnostic]]


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
    """Decorator registering a check function as one Annex B SCR rule."""

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
            )
        )
        return check

    return decorator


def all_rules() -> List[Rule]:
    return list(_REGISTRY)
