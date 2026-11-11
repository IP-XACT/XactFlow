from __future__ import annotations

import abc
import sys
import warnings
from importlib.metadata import entry_points
from pathlib import Path
from typing import Dict, Type

from .library import Library

_ENTRY_POINT_GROUP = "xactflow.exporters"


class Exporter(abc.ABC):
    """Base class for a XactFlow exporter plugin.

    An exporter writes an output (RTL, documentation, IP-XACT XML, etc) for the targets of a
    Library: the documents an importer, or the CLI, added with target=True. It picks the kinds
    it supports, e.g. library.targets(ipxact.Component), and finds everything they refer to in
    library.documents(); a design can be linked with xactflow.link(design, library).

    Each exporter documents the kinds of target it supports, and raises a plain TypeError when
    the library holds none of them. The CLI relies on that exception type to print a one-line
    message naming the exporter, instead of a generic error.

    An exporter that writes IP-XACT should check what it wrote with
    xactflow.SCR.run_single_doc_checks and run_post_config_checks.

    XactFlow ships no exporters. Packages register their subclasses under the
    "xactflow.exporters" entry point group, and discover_exporters() below finds them.
    """

    name: str

    @abc.abstractmethod
    def export(self, library: Library, output_dir: Path, **options: object) -> None:
        """Generate this exporter's output for the targets of `library` into `output_dir`."""


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
