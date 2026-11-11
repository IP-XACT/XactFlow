from pathlib import Path

import ipxact
import pytest

from xactflow.exporter import Exporter, discover_exporters
from xactflow.library import Library


def test_exporter_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        Exporter()


def test_concrete_exporter_writes_the_targets_of_the_library_it_is_given():
    class FakeExporter(Exporter):
        name = "fake"

        def __init__(self):
            self.calls = []

        def export(self, library, output_dir, **options):
            for component in library.targets(ipxact.Component):
                self.calls.append((str(component.vlnv), output_dir, options))

    library = Library()
    library.add(ipxact.Component(vlnv=ipxact.VLNV.parse("example.org:ip:looked_up:1.0")))
    library.add(ipxact.Component(vlnv=ipxact.VLNV.parse("example.org:ip:written:1.0")), target=True)

    exporter = FakeExporter()
    exporter.export(library, Path("/tmp/out"), foo="bar")
    assert exporter.calls == [("example.org:ip:written:1.0", Path("/tmp/out"), {"foo": "bar"})]


class _FakeExporter(Exporter):
    name = "fake"

    def export(self, library, output_dir, **options):
        pass


class _NotAnExporter:
    pass


class _FakeEntryPoint:
    def __init__(self, name, target):
        self.name = name
        self._target = target

    def load(self):
        return self._target


def test_discover_exporters_returns_registered_subclasses(monkeypatch):
    def fake_entry_points_for_group(group):
        assert group == "xactflow.exporters"
        return [_FakeEntryPoint("fake", _FakeExporter)]

    monkeypatch.setattr("xactflow.exporter._entry_points_for_group", fake_entry_points_for_group)

    exporters = discover_exporters()

    assert exporters == {"fake": _FakeExporter}


class _FailingEntryPoint:
    def __init__(self, name):
        self.name = name

    def load(self):
        raise ImportError("No module named 'missing_plugin'")


def test_discover_exporters_skips_entry_point_that_is_not_an_exporter(monkeypatch):
    def fake_entry_points_for_group(group):
        return [_FakeEntryPoint("bad", _NotAnExporter), _FakeEntryPoint("fake", _FakeExporter)]

    monkeypatch.setattr("xactflow.exporter._entry_points_for_group", fake_entry_points_for_group)

    with pytest.warns(UserWarning, match="skipping entry point 'bad'.*not resolve to an Exporter subclass"):
        exporters = discover_exporters()
    assert exporters == {"fake": _FakeExporter}


def test_discover_exporters_skips_entry_point_that_fails_to_load(monkeypatch):
    def fake_entry_points_for_group(group):
        return [_FailingEntryPoint("broken"), _FakeEntryPoint("fake", _FakeExporter)]

    monkeypatch.setattr("xactflow.exporter._entry_points_for_group", fake_entry_points_for_group)

    with pytest.warns(UserWarning, match="skipping entry point 'broken'.*No module named 'missing_plugin'"):
        exporters = discover_exporters()
    assert exporters == {"fake": _FakeExporter}


def test_discover_exporters_returns_empty_dict_when_none_installed(monkeypatch):
    monkeypatch.setattr("xactflow.exporter._entry_points_for_group", lambda group: [])

    assert discover_exporters() == {}
