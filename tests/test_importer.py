from pathlib import Path

import pytest

from xactflow.importer import Importer, discover_importers


def test_importer_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        Importer()


def test_concrete_importer_subclass_can_be_instantiated_and_called():
    class FakeImporter(Importer):
        name = "fake"

        def __init__(self):
            self.calls = []

        def import_(self, source_path, **options):
            self.calls.append((source_path, options))
            return "fake-object-model"

    importer = FakeImporter()
    result = importer.import_(Path("/tmp/source.sv"), foo="bar")
    assert result == "fake-object-model"
    assert importer.calls == [(Path("/tmp/source.sv"), {"foo": "bar"})]


class _FakeImporter(Importer):
    name = "fake"

    def import_(self, source_path, **options):
        return None


class _NotAnImporter:
    pass


class _FakeEntryPoint:
    def __init__(self, name, target):
        self.name = name
        self._target = target

    def load(self):
        return self._target


def test_discover_importers_returns_registered_subclasses(monkeypatch):
    def fake_entry_points_for_group(group):
        assert group == "xactflow.importers"
        return [_FakeEntryPoint("fake", _FakeImporter)]

    monkeypatch.setattr("xactflow.importer._entry_points_for_group", fake_entry_points_for_group)

    importers = discover_importers()

    assert importers == {"fake": _FakeImporter}


def test_discover_importers_rejects_entry_point_that_is_not_an_importer(monkeypatch):
    def fake_entry_points_for_group(group):
        return [_FakeEntryPoint("bad", _NotAnImporter)]

    monkeypatch.setattr("xactflow.importer._entry_points_for_group", fake_entry_points_for_group)

    with pytest.raises(TypeError):
        discover_importers()


def test_discover_importers_returns_empty_dict_when_none_installed(monkeypatch):
    monkeypatch.setattr("xactflow.importer._entry_points_for_group", lambda group: [])

    assert discover_importers() == {}
