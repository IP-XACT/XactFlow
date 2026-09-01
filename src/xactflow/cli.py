from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Type

import ipxact

from . import SCR
from .diagnostics import Diagnostic, Severity
from .elaborate import elaborate
from .exporter import Exporter, discover_exporters
from .importer import Importer, discover_importers
from .library import Library

_BUILTIN_COMMANDS = {"elaborate", "check"}


def _print_diagnostics(diagnostics: List[Diagnostic]) -> None:
    for diagnostic in diagnostics:
        print(str(diagnostic), file=sys.stderr)


def _has_errors(diagnostics: List[Diagnostic]) -> bool:
    return any(diagnostic.severity is Severity.ERROR for diagnostic in diagnostics)


def _parse_option(value: str) -> Tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"expected KEY=VALUE, got {value!r}")
    key, _, val = value.partition("=")
    return key, val


def _dedupe_diagnostics(diagnostics: List[Diagnostic]) -> List[Diagnostic]:
    # library.diagnostics and elaborated.diagnostics can both contain single-doc SCR checks for
    # a same design, since Library.scan and elaborate() each run single-doc checks independently.
    # Diagnostic is a frozen dataclass, so exact-duplicate findings can be collapsed by value
    # while preserving first-seen order.
    seen: set = set()
    deduped = []
    for diagnostic in diagnostics:
        if diagnostic in seen:
            continue
        seen.add(diagnostic)
        deduped.append(diagnostic)
    return deduped


def _elaborate_from_args(args: argparse.Namespace):
    library = Library.scan(*args.lib)
    design = ipxact.parse_file(args.design)
    design_configuration = ipxact.parse_file(args.config) if args.config else None
    elaborated = elaborate(design, library, design_configuration)
    diagnostics = _dedupe_diagnostics(library.diagnostics + elaborated.diagnostics)
    return elaborated, diagnostics


def _cmd_elaborate(args: argparse.Namespace) -> int:
    elaborated, diagnostics = _elaborate_from_args(args)
    _print_diagnostics(diagnostics)
    if _has_errors(diagnostics):
        return 1
    print(
        f"elaborated '{elaborated.vlnv}' with no errors "
        f"({len(elaborated.instances)} instances, {len(elaborated.interconnections)} interconnections)"
    )
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    document = ipxact.parse_file(args.file)
    diagnostics = SCR.run_single_doc_checks(document)
    _print_diagnostics(diagnostics)
    if _has_errors(diagnostics):
        return 1
    print(f"no single-document SCR violations found in {args.file}")
    return 0


def _cmd_run_exporter(args: argparse.Namespace) -> int:
    elaborated, diagnostics = _elaborate_from_args(args)
    _print_diagnostics(diagnostics)
    if _has_errors(diagnostics):
        print("not exporting: elaboration reported errors", file=sys.stderr)
        return 1

    options = dict(args.option or [])
    args.exporter_class().export(elaborated, Path(args.output), **options)
    print(f"exported '{elaborated.vlnv}' via '{args.command}' to {args.output}")
    return 0


def _cmd_run_importer(args: argparse.Namespace) -> int:
    options = dict(args.option or [])
    result = args.importer_class().import_(Path(args.source), **options)
    print(f"imported '{args.source}' via '{args.command}': {type(result).__name__}")
    return 0


def _add_builtin_subparsers(subparsers: "argparse._SubParsersAction") -> None:
    elaborate_parser = subparsers.add_parser(
        "elaborate", help="resolve a design against a library and report SCR diagnostics"
    )
    elaborate_parser.add_argument("design", help="path to the top-level design XML file")
    elaborate_parser.add_argument(
        "--lib",
        action="append",
        default=[],
        metavar="DIR",
        help="directory to scan for IP-XACT files; may be given multiple times",
    )
    elaborate_parser.add_argument(
        "--config", default=None, metavar="FILE", help="path to the matching designConfiguration XML file"
    )
    elaborate_parser.set_defaults(func=_cmd_elaborate)

    check_parser = subparsers.add_parser(
        "check", help="run single-document SCR checks on one IP-XACT file, no library needed"
    )
    check_parser.add_argument("file", help="path to an IP-XACT XML file")
    check_parser.set_defaults(func=_cmd_check)


def _add_exporter_subparser(
    subparsers: "argparse._SubParsersAction", name: str, exporter_class: Type[Exporter]
) -> None:
    parser = subparsers.add_parser(name, help=f"elaborate a design and run the '{name}' exporter on it")
    parser.add_argument("design", help="path to the top-level design XML file")
    parser.add_argument("--lib", action="append", default=[], metavar="DIR")
    parser.add_argument("--config", default=None, metavar="FILE")
    parser.add_argument("--output", default=".", metavar="DIR")
    parser.add_argument(
        "--option", action="append", type=_parse_option, metavar="KEY=VALUE",
        help="an exporter-specific option, may be given multiple times",
    )
    parser.set_defaults(func=_cmd_run_exporter, exporter_class=exporter_class)


def _add_importer_subparser(
    subparsers: "argparse._SubParsersAction", name: str, importer_class: Type[Importer]
) -> None:
    parser = subparsers.add_parser(name, help=f"run the '{name}' importer on a non-IP-XACT source file")
    parser.add_argument("source", help="path to the source file to import")
    parser.add_argument(
        "--option", action="append", type=_parse_option, metavar="KEY=VALUE",
        help="an importer-specific option, may be given multiple times",
    )
    parser.set_defaults(func=_cmd_run_importer, importer_class=importer_class)


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI. Every installed exporter or importer becomes its own top-level subcommand,
    so a plugin package is usable the moment it's installed with no separate registration step.
    Elaborate and check are XactFlow's own built-in subcommands, not plugins.
    """
    parser = argparse.ArgumentParser(
        prog="xactflow",
        description="Multi-file IP-XACT elaboration and semantic consistency checking.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_builtin_subparsers(subparsers)

    registered_names = set(_BUILTIN_COMMANDS)
    for name, exporter_class in sorted(discover_exporters().items()):
        if name in registered_names:
            print(
                f"warning: exporter '{name}' conflicts with an existing xactflow subcommand, skipping",
                file=sys.stderr,
            )
            continue
        _add_exporter_subparser(subparsers, name, exporter_class)
        registered_names.add(name)

    for name, importer_class in sorted(discover_importers().items()):
        if name in registered_names:
            print(
                f"warning: importer '{name}' conflicts with an existing xactflow subcommand, skipping",
                file=sys.stderr,
            )
            continue
        _add_importer_subparser(subparsers, name, importer_class)
        registered_names.add(name)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        parser = _build_parser()
        args = parser.parse_args(argv)
        return args.func(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
