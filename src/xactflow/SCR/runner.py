from __future__ import annotations

from typing import List

from ..diagnostics import Diagnostic
from .registry import all_rules


def run_single_doc_checks(document: object) -> List[Diagnostic]:
    """Run every SCR rule checkable on one IP-XACT document alone (single_doc_check rules)."""
    diagnostics: List[Diagnostic] = []
    for r in all_rules():
        if r.single_doc_check:
            diagnostics.extend(r.check(document))
    return diagnostics


def run_post_config_checks(elaborated: object) -> List[Diagnostic]:
    """Run every SCR rule that needs the relationships between documents.

    Takes an elaborate.ElaboratedDesign (accepted as object here to avoid a circular import
    between xactflow.SCR and xactflow.elaborate, since elaborate.resolver itself calls this).
    """
    diagnostics: List[Diagnostic] = []
    for r in all_rules():
        if not r.single_doc_check:
            diagnostics.extend(r.check(elaborated))
    return diagnostics
