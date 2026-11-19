from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Optional, Tuple, Type, Union

import ipxact
from lxml import etree

from . import SCR
from .diagnostics import Diagnostic, Severity

# Mirrors the parser configuration.
_XML_PARSER = etree.XMLParser(remove_comments=True)

# IEEE 1685-2022's XML namespace. Files outside this namespace are not IP-XACT at all.
_IPXACT_NAMESPACE = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

# Namespace prefixes of the other IP-XACT versions (1685-2009/2014, SPIRIT 1.x).
_OTHER_IPXACT_NAMESPACE_PREFIXES = (
    "http://www.accellera.org/XMLSchema/IPXACT/",
    "http://www.spiritconsortium.org/XMLSchema/SPIRIT/",
)


@dataclass
class LibraryEntry:
    """One IP-XACT document indexed in the library.

    path is the file the document was parsed from, or None for a document added in memory
    through Library.add.

    target marks a document as the output of the flow, the one an exporter writes, as opposed to
    one that is only there to be looked up, e.g. a component scanned from a --lib folder.
    """

    path: Optional[Path]
    document: object
    target: bool = False


@dataclass
class Library:
    """A VLNV-indexed collection of IP-XACT documents.

    Documents come from three sources, all with the same checks: the .xml files under the
    directories given to scan, the files given to scan(files=...) or add_file, and documents that
    only exist in memory (e.g. produced by an importer), given to add. Each IEEE 1685-2022
    document is indexed by its VLNV. Files that fail to parse and VLNV collisions (SCR 1.1
    uniqueVLNV) are recorded as diagnostics instead of raising; only a missing directory or file
    raises.

    The library is what importers and exporters share: an importer adds the documents it
    produces with target=True, and an exporter writes the targets() it supports, looking up
    everything else they refer to in documents().
    """

    entries: "dict[ipxact.VLNV, LibraryEntry]" = field(default_factory=dict)
    diagnostics: "list[Diagnostic]" = field(default_factory=list)
    # Resolved paths of the files already read, so overlapping roots read each file once.
    _read_files: "set[Path]" = field(default_factory=set, init=False, repr=False)

    @classmethod
    def scan(cls, *roots: Union[str, Path], files: Iterable[Union[str, Path]] = ()) -> "Library":
        """Read every .xml file under roots, then each of files, which are read directly without
        scanning a directory, e.g. a file list given by a build system.
        """
        root_paths = [Path(root) for root in roots]
        for root in root_paths:
            if not root.exists():
                raise FileNotFoundError(f"library scan root does not exist: {root}")
            if not root.is_dir():
                raise NotADirectoryError(f"library scan root is not a directory: {root}")
        file_paths = [Path(file) for file in files]
        for path in file_paths:
            if not path.exists():
                raise FileNotFoundError(f"library file does not exist: {path}")
            if path.is_dir():
                raise IsADirectoryError(f"library file is a directory, not a file: {path}")

        library = cls()
        for root in root_paths:
            indexed_any = False
            for path in sorted(root.rglob("*.xml")):
                indexed_any |= library.add_file(path)
            if not indexed_any:
                # An empty root can be intended (e.g. a library folder not populated yet), so this
                # is only a warning, unlike a root that does not exist at all.
                library.diagnostics.append(
                    Diagnostic(
                        message=f"no IEEE 1685-2022 IP-XACT document was indexed from {root}",
                        severity=Severity.WARNING,
                        location=str(root),
                    )
                )
        for path in file_paths:
            reported = len(library.diagnostics)
            if not library.add_file(path) and len(library.diagnostics) == reported:
                # A file given by name is meant to be IP-XACT, so unlike one found under a root it
                # is not skipped silently; a file add_file already reported on is not reported twice.
                library.diagnostics.append(
                    Diagnostic(
                        message=f"skipped {path}: not an IEEE 1685-2022 IP-XACT document",
                        severity=Severity.WARNING,
                        location=str(path),
                    )
                )
        return library

    def add(
        self, document: object, path: Optional[Path] = None, *, replace: bool = False, target: bool = False
    ) -> bool:
        """Index an already-parsed IP-XACT document, e.g. one produced in memory by an importer.

        With replace=True the existing entry is overwritten, for when the document is regenerated
        from a source that changes the scanned one. With target=True the document is one of
        targets().

        Returns True if the document was indexed, False if it was rejected as a duplicate.
        """
        self.diagnostics.extend(SCR.run_single_doc_checks(document))

        vlnv = document.vlnv
        existing = self.entries.get(vlnv)
        if existing is not None and not replace:
            self.diagnostics.append(
                Diagnostic(
                    message=f"duplicate VLNV {vlnv}: already loaded from {_describe(existing.path)}, "
                    f"also found in {_describe(path)}",
                    severity=Severity.ERROR,
                    location=str(vlnv),
                    rule_id="SCR 1.1",
                    rule_name="uniqueVLNV",
                )
            )
            return False

        self.entries[vlnv] = LibraryEntry(path=path, document=document, target=target)
        return True

    def add_file(self, path: Union[str, Path], *, replace: bool = False, target: bool = False) -> bool:
        """Parse one file and index it, with the same checks as scan. A file already read, by any
        path, is not read again unless replace=True; with target=True its document still becomes
        a target, e.g. a design given on the command line that is also under a --lib folder.

        Returns True if the file's document is in the library, False if the file is not IP-XACT
        1685-2022, fails to parse, or has a duplicate VLNV.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"library file does not exist: {path}")
        resolved = path.resolve()
        if resolved in self._read_files and not replace:
            found = False
            for entry in self.entries.values():
                if entry.path is not None and entry.path.resolve() == resolved:
                    entry.target |= target
                    found = True
            return found
        self._read_files.add(resolved)
        document = self._parse_file(path)
        return document is not None and self.add(document, path, replace=replace, target=target)

    def _parse_file(self, path: Path) -> Optional[object]:
        """Parse one file into an IP-XACT 1685-2022 document, or return None if it is not one.

        IP-XACT 1685-2022 files that are not well-formed or fail to parse, and files of another
        IP-XACT version, are recorded as warnings; any other file is skipped silently.
        """
        try:
            root = etree.parse(str(path), parser=_XML_PARSER).getroot()
        except etree.XMLSyntaxError as exc:
            if _IPXACT_NAMESPACE.encode() not in path.read_bytes():
                return None  # not an IP-XACT 1685-2022 file, not ours to report on.
            self.diagnostics.append(
                Diagnostic(
                    message=f"skipped {path}: not well-formed XML: {exc}",
                    severity=Severity.WARNING,
                    location=str(path),
                )
            )
            return None

        namespace = etree.QName(root).namespace
        if namespace != _IPXACT_NAMESPACE:
            if namespace is not None and namespace.startswith(_OTHER_IPXACT_NAMESPACE_PREFIXES):
                self.diagnostics.append(
                    Diagnostic(
                        message=f"skipped {path}: IP-XACT namespace {namespace} is not "
                        f"IEEE 1685-2022, the only version supported",
                        severity=Severity.WARNING,
                        location=str(path),
                    )
                )
            return None  # well-formed XML, but not IP-XACT 1685-2022, skip.

        try:
            document = ipxact.parse_element(root)
        except Exception as exc:
            self.diagnostics.append(
                Diagnostic(
                    message=f"failed to parse {path}: {exc}",
                    severity=Severity.WARNING,
                    location=str(path),
                )
            )
            return None

        return document

    def documents(self, kind: Union[Type, Tuple[Type, ...], None] = None) -> Iterator[object]:
        """Every document, or only those that are instances of kind, e.g. ipxact.Component."""
        return (
            entry.document
            for entry in self.entries.values()
            if kind is None or isinstance(entry.document, kind)
        )

    def targets(self, kind: Union[Type, Tuple[Type, ...], None] = None) -> Iterator[object]:
        """The documents added with target=True, or only those that are instances of kind."""
        return (
            entry.document
            for entry in self.entries.values()
            if entry.target and (kind is None or isinstance(entry.document, kind))
        )

    def get(self, vlnv: "ipxact.VLNV") -> Optional[object]:
        entry = self.entries.get(vlnv)
        return entry.document if entry is not None else None

    def get_component(self, vlnv: "ipxact.VLNV") -> Optional["ipxact.Component"]:
        document = self.get(vlnv)
        return document if isinstance(document, ipxact.Component) else None

    def get_design(self, vlnv: "ipxact.VLNV") -> Optional["ipxact.Design"]:
        document = self.get(vlnv)
        return document if isinstance(document, ipxact.Design) else None

    def get_design_configuration(self, vlnv: "ipxact.VLNV") -> Optional["ipxact.DesignConfiguration"]:
        document = self.get(vlnv)
        return document if isinstance(document, ipxact.DesignConfiguration) else None

    def get_bus_definition(self, vlnv: "ipxact.VLNV") -> Optional["ipxact.BusDefinition"]:
        document = self.get(vlnv)
        return document if isinstance(document, ipxact.BusDefinition) else None

    def get_abstraction_definition(self, vlnv: "ipxact.VLNV") -> Optional["ipxact.AbstractionDefinition"]:
        document = self.get(vlnv)
        return document if isinstance(document, ipxact.AbstractionDefinition) else None


def _describe(path: Optional[Path]) -> str:
    return str(path) if path is not None else "<in-memory>"
