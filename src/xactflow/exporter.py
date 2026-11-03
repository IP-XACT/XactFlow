from __future__ import annotations

import abc
import sys
import warnings
from importlib.metadata import entry_points
from pathlib import Path
from typing import Dict, Type

_ENTRY_POINT_GROUP = "xactflow.exporters"


class Exporter(abc.ABC):
    """Base class for a XactFlow exporter plugin.

    An exporter turns some IP-XACT-flavored Python object into an output artifact (RTL,
    documentation, another IP-XACT file, etc). `subject` is deliberately untyped: it may be an
    LinkedDesign, a bare ipxact.Component or ipxact.Design, or anything else a given exporter
    chooses to support. It is each exporter's own job to check what it was actually handed and
    document what it accepts, and to raise a plain TypeError when `subject` is not one of the
    types it supports. That specific exception type is a load-bearing convention, not just a
    style choice: the CLI's importer-to-exporter chaining (`--then`) catches TypeError
    specifically to report a clear, one-line rejection instead of a generic error.

    XactFlow itself ships no exporters; third-party packages register subclasses under the
    "xactflow.exporters" entry point group in their own pyproject.toml, and discover_exporters()
    below finds them without XactFlow depending on them.

    An exporter that itself generates IP-XACT output should re-run SCR checking on what it
    generated, using the public, standalone xactflow.SCR.run_single_doc_checks /
    run_post_config_checks functions.
    """

    name: str

    @abc.abstractmethod
    def export(self, subject: object, output_dir: Path, **options: object) -> None:
        """Generate this exporter's output for `subject` into `output_dir`."""


def _entry_points_for_group(group: str):
    # entry_points(group=...) is only available from Python 3.10; on 3.9 entry_points()
    # returns a dict keyed by group name instead.
    if sys.version_info >= (3, 10):
        return entry_points(group=group)
    return entry_points().get(group, [])


def discover_exporters() -> Dict[str, Type[Exporter]]:
    """Find every Exporter subclass registered under the "xactflow.exporters" entry point group:

        [project.entry-points."xactflow.exporters"]
        component = "xactflow_component:ComponentExporter"

    Keyed by entry point name (e.g. "component"), the name the CLI uses, not by Exporter.name.
    An entry point that fails to load, or is not an Exporter subclass, is skipped with a warning.
    """
    exporters: Dict[str, Type[Exporter]] = {}
    for entry_point in _entry_points_for_group(_ENTRY_POINT_GROUP):
        try:
            exporter_class = entry_point.load()
        except Exception as exc:
            warnings.warn(
                f"skipping entry point '{entry_point.name}' in group '{_ENTRY_POINT_GROUP}': "
                f"failed to load: {exc}"
            )
            continue
        if not (isinstance(exporter_class, type) and issubclass(exporter_class, Exporter)):
            warnings.warn(
                f"skipping entry point '{entry_point.name}' in group '{_ENTRY_POINT_GROUP}': "
                f"does not resolve to an Exporter subclass: {exporter_class!r}"
            )
            continue
        exporters[entry_point.name] = exporter_class
    return exporters
