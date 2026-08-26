from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Union

import ipxact
from lxml import etree

from .diagnostics import Diagnostic, Severity

# Mirrors the parser configuration ipxact.parse_file uses internally (not exposed publicly
# by ipxact-compiler, so duplicated here on purpose): comments left in place can silently
# corrupt a preceding element's text, so they are stripped up front here too, since the
# parsed root below is reused for ipxact.parse_element instead of re-parsing.
_XML_PARSER = etree.XMLParser(remove_comments=True)

# IEEE 1685-2022's XML namespace. Files outside this namespace are not IP-XACT at all (e.g.
# unrelated tooling config sitting in a scanned directory) and are silently skipped rather
# than reported, since they were never meant to be read by this library.
_IPXACT_NAMESPACE = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass
class LibraryEntry:
    """One successfully parsed IP-XACT document found while scanning the library."""

    path: Path
    document: object


@dataclass
class Library:
    """A VLNV-indexed collection of IP-XACT documents discovered by scanning directories.

    Mirrors an IP-XACT library/catalog of files without requiring an actual ipxact:catalog
    document: every .xml file under the scanned roots is parsed with ipxact.parse_file, and
    documents that parse successfully are indexed by their VLNV. Files that fail to parse, and
    VLNV collisions (SCR 1.1 uniqueVLNV), are recorded as diagnostics instead of raising.
    """

    entries: "dict[ipxact.VLNV, LibraryEntry]" = field(default_factory=dict)
    diagnostics: "list[Diagnostic]" = field(default_factory=list)

    @classmethod
    def scan(cls, *roots: Union[str, Path]) -> "Library":
        library = cls()
        for root in roots:
            for path in sorted(Path(root).rglob("*.xml")):
                library._add_file(path)
        return library

    def _add_file(self, path: Path) -> None:
        try:
            root = etree.parse(str(path), parser=_XML_PARSER).getroot()
        except etree.XMLSyntaxError:
            return  # not well-formed XML at all; not ours to report on

        if etree.QName(root).namespace != _IPXACT_NAMESPACE:
            return  # well-formed XML, but not IP-XACT; silently skip

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
            return

        vlnv = document.vlnv
        existing = self.entries.get(vlnv)
        if existing is not None:
            self.diagnostics.append(
                Diagnostic(
                    message=f"duplicate VLNV {vlnv}: already loaded from {existing.path}, "
                    f"also found in {path}",
                    severity=Severity.ERROR,
                    location=str(vlnv),
                    rule_id="SCR 1.1",
                    rule_name="uniqueVLNV",
                )
            )
            return

        self.entries[vlnv] = LibraryEntry(path=path, document=document)

    def documents(self) -> Iterable[object]:
        return (entry.document for entry in self.entries.values())

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
