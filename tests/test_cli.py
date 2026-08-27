from pathlib import Path

import pytest

from xactflow.cli import main
from xactflow.exporter import Exporter
from xactflow.importer import Importer

FIXTURES = Path(__file__).parent / "fixtures"


def test_elaborate_happy_path_exits_zero(capsys):
    exit_code = main(
        [
            "elaborate",
            str(FIXTURES / "basic" / "top_design.xml"),
            "--lib",
            str(FIXTURES / "basic"),
        ]
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "elaborated 'example.org:soc:top:1.0'" in out
    assert "no errors" in out


def test_elaborate_reports_unresolvable_component_ref_and_exits_nonzero(capsys):
    exit_code = main(
        [
            "elaborate",
            str(FIXTURES / "cli" / "broken_design.xml"),
            "--lib",
            str(FIXTURES / "basic"),
        ]
    )

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "SCR 1.9" in err


def test_check_happy_path_exits_zero(capsys):
    exit_code = main(["check", str(FIXTURES / "basic" / "top_design.xml")])

    assert exit_code == 0
    assert "no single-document SCR violations" in capsys.readouterr().out


def test_check_reports_duplicate_interface_and_exits_nonzero(capsys):
    exit_code = main(["check", str(FIXTURES / "cli" / "duplicate_interface_design.xml")])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "SCR 2.3" in err


def test_main_reports_a_clean_error_for_a_missing_file(capsys):
    exit_code = main(["check", str(FIXTURES / "does_not_exist.xml")])

    assert exit_code == 1
    assert capsys.readouterr().err.startswith("error: ")


def test_no_plugin_subcommands_when_none_are_installed(capsys):
    # with no exporters/importers registered (the real state of this repo, which ships none),
    # only the built-in elaborate/check subcommands should exist.
    with pytest.raises(SystemExit):
        main(["fake-exporter", str(FIXTURES / "basic" / "top_design.xml")])
    assert "invalid choice" in capsys.readouterr().err


class _FakeExporter(Exporter):
    name = "fake"
    exported: list = []

    def export(self, elaborated, output_dir, **options):
        type(self).exported.append((elaborated.vlnv, output_dir, options))


def test_installed_exporter_becomes_its_own_top_level_subcommand(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("xactflow.cli.discover_exporters", lambda: {"fake-exporter": _FakeExporter})
    _FakeExporter.exported.clear()

    exit_code = main(
        [
            "fake-exporter",
            str(FIXTURES / "basic" / "top_design.xml"),
            "--lib",
            str(FIXTURES / "basic"),
            "--output",
            str(tmp_path),
            "--option",
            "flavor=minimal",
        ]
    )

    assert exit_code == 0
    assert len(_FakeExporter.exported) == 1
    vlnv, output_dir, options = _FakeExporter.exported[0]
    assert str(vlnv) == "example.org:soc:top:1.0"
    assert output_dir == tmp_path
    assert options == {"flavor": "minimal"}
    assert "exported 'example.org:soc:top:1.0' via 'fake-exporter'" in capsys.readouterr().out


def test_installed_exporter_does_not_run_when_elaboration_has_errors(monkeypatch, tmp_path):
    monkeypatch.setattr("xactflow.cli.discover_exporters", lambda: {"fake-exporter": _FakeExporter})
    _FakeExporter.exported.clear()

    exit_code = main(
        [
            "fake-exporter",
            str(FIXTURES / "cli" / "broken_design.xml"),
            "--lib",
            str(FIXTURES / "basic"),
            "--output",
            str(tmp_path),
        ]
    )

    assert exit_code == 1
    assert _FakeExporter.exported == []


class _FakeImporter(Importer):
    name = "fake"
    imported: list = []

    def import_(self, source_path, **options):
        type(self).imported.append((source_path, options))
        return "fake-object-model"


def test_installed_importer_becomes_its_own_top_level_subcommand(monkeypatch, capsys):
    monkeypatch.setattr("xactflow.cli.discover_importers", lambda: {"fake-importer": _FakeImporter})
    _FakeImporter.imported.clear()

    exit_code = main(["fake-importer", str(FIXTURES / "basic" / "top_design.xml"), "--option", "mode=strict"])

    assert exit_code == 0
    assert _FakeImporter.imported == [
        (Path(str(FIXTURES / "basic" / "top_design.xml")), {"mode": "strict"})
    ]
    out = capsys.readouterr().out
    assert "imported" in out
    assert "via 'fake-importer': str" in out


def test_plugin_name_colliding_with_a_builtin_command_is_skipped(monkeypatch, capsys):
    monkeypatch.setattr("xactflow.cli.discover_exporters", lambda: {"check": _FakeExporter})
    monkeypatch.setattr("xactflow.cli.discover_importers", lambda: {})

    # "check" stays the real built-in command, not the fake exporter.
    exit_code = main(["check", str(FIXTURES / "basic" / "top_design.xml")])

    assert exit_code == 0
    assert "conflicts with an existing xactflow subcommand" in capsys.readouterr().err
