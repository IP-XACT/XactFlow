from __future__ import annotations

import abc
import sys
import warnings
from importlib.metadata import entry_points
from pathlib import Path
from typing import Dict, Type

_ENTRY_POINT_GROUP = "xactflow.importers"


class Importer(abc.ABC):
    """Base class for a XactFlow importer plugin.

    An importer reads some non-IP-XACT source (a custom design description, an annotated
    SystemVerilog file, etc) and produces an IP-XACT object model instance from it.
    XactFlow itself ships no importers; third-party packages register subclasses under the
    "xactflow.importers" entry point group in their own pyproject.toml, and discover_importers()
    below finds them without XactFlow depending on them.
    """

    name: str

    @abc.abstractmethod
    def import_(self, source_path: Path, **options: object) -> object:
        """Read `source_path` and return the IP-XACT object model it describes."""


def _entry_points_for_group(group: str):
    # entry_points(group=...) is only available from Python 3.10; on 3.9 entry_points()
    # returns a dict keyed by group name instead.
    if sys.version_info >= (3, 10):
        return entry_points(group=group)
    return entry_points().get(group, [])


def discover_importers() -> Dict[str, Type[Importer]]:
    """Find every Importer subclass registered under the "xactflow.importers" entry point group:

        [project.entry-points."xactflow.importers"]
        sv = "xactflow_sv:SVImporter"

    Keyed by entry point name (e.g. "sv"), the name the CLI uses, not by Importer.name. An
    entry point that fails to load, or is not an Importer subclass, is skipped with a warning.
    """
    importers: Dict[str, Type[Importer]] = {}
    for entry_point in _entry_points_for_group(_ENTRY_POINT_GROUP):
        try:
            importer_class = entry_point.load()
        except Exception as exc:
            warnings.warn(
                f"skipping entry point '{entry_point.name}' in group '{_ENTRY_POINT_GROUP}': "
                f"failed to load: {exc}"
            )
            continue
        if not (isinstance(importer_class, type) and issubclass(importer_class, Importer)):
            warnings.warn(
                f"skipping entry point '{entry_point.name}' in group '{_ENTRY_POINT_GROUP}': "
                f"does not resolve to an Importer subclass: {importer_class!r}"
            )
            continue
        importers[entry_point.name] = importer_class
    return importers
