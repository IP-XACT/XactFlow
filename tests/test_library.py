from pathlib import Path

import ipxact

from xactflow.diagnostics import Severity
from xactflow.library import Library

FIXTURES = Path(__file__).parent / "fixtures"


def test_scan_indexes_every_document_by_vlnv():
    library = Library.scan(FIXTURES / "basic")

    assert library.diagnostics == []
    assert library.get_component(ipxact.VLNV.parse("example.org:ip:initiator_comp:1.0")) is not None
    assert library.get_component(ipxact.VLNV.parse("example.org:ip:target_comp:1.0")) is not None
    assert library.get_design(ipxact.VLNV.parse("example.org:soc:top:1.0")) is not None
    assert (
        library.get_bus_definition(ipxact.VLNV.parse("example.org:bus:simplebus:1.0")) is not None
    )
    assert (
        library.get_abstraction_definition(ipxact.VLNV.parse("example.org:bus:simplebus_rtl:1.0"))
        is not None
    )


def test_get_returns_none_for_unknown_vlnv():
    library = Library.scan(FIXTURES / "basic")
    assert library.get_component(ipxact.VLNV.parse("example.org:ip:missing:1.0")) is None


def test_get_component_returns_none_for_wrong_document_type():
    library = Library.scan(FIXTURES / "basic")
    bus_vlnv = ipxact.VLNV.parse("example.org:bus:simplebus:1.0")
    assert library.get_component(bus_vlnv) is None
    assert library.get_bus_definition(bus_vlnv) is not None


def test_non_ipxact_xml_file_is_silently_skipped():
    """A well-formed XML file outside the IP-XACT namespace was never meant to be read by
    this library (e.g. unrelated tooling config sitting in a scanned directory), so it is
    skipped without a diagnostic rather than reported as broken.
    """
    library = Library.scan(FIXTURES / "not_ipxact")

    assert library.diagnostics == []
    assert library.entries == {}


def test_unsupported_ipxact_document_type_is_recorded_as_a_warning_and_does_not_raise():
    """A file in the IP-XACT namespace whose root element ipxact-compiler does not support
    (e.g. ipxact:catalog) is a real gap worth surfacing, unlike a non-IP-XACT file.
    """
    library = Library.scan(FIXTURES / "broken")

    assert len(library.diagnostics) == 1
    diagnostic = library.diagnostics[0]
    assert diagnostic.severity is Severity.WARNING
    assert diagnostic.rule_id is None
    assert "unsupported_catalog.xml" in diagnostic.location


def test_duplicate_vlnv_is_recorded_as_an_scr_1_1_error():
    library = Library.scan(FIXTURES / "basic", FIXTURES / "duplicate")

    duplicates = [d for d in library.diagnostics if d.rule_id == "SCR 1.1"]
    assert len(duplicates) == 1
    assert duplicates[0].severity is Severity.ERROR
    assert duplicates[0].rule_name == "uniqueVLNV"

    # the first-scanned file wins; the real fixture (not the stub duplicate) stays indexed.
    component = library.get_component(ipxact.VLNV.parse("example.org:ip:initiator_comp:1.0"))
    assert component.bus_interfaces
