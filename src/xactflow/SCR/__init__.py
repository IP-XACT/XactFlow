from . import (  # noqa: F401  (registers every Annex B rule as an import side effect)
    scr_01,
    scr_02,
    scr_03,
    scr_04,
    scr_05,
    scr_06,
    scr_07,
    scr_08,
    scr_09,
    scr_10,
    scr_11,
    scr_12,
    scr_13,
    scr_14,
    scr_15,
)
from .registry import Rule, all_rules, rule, stub
from .runner import run_post_config_checks, run_single_doc_checks

__all__ = [
    "Rule",
    "all_rules",
    "rule",
    "stub",
    "run_post_config_checks",
    "run_single_doc_checks",
]
