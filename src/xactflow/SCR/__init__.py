from . import rules  # noqa: F401  (registers the built-in rules as an import side effect)
from .registry import Rule, all_rules, rule
from .runner import run_post_config_checks, run_single_doc_checks

__all__ = [
    "Rule",
    "all_rules",
    "rule",
    "run_post_config_checks",
    "run_single_doc_checks",
]
