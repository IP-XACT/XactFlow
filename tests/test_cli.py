from pathlib import Path

import ipxact
import pytest

from xactflow.cli import main
from xactflow.exporter import Exporter
from xactflow.importer import Importer

FIXTURES = Path(__file__).parent / "fixtures"


def test_link_happy_path_exits_zero(capsys):
    exit_code = main(
        [
            "link",
            str(FIXTURES / "basic" / "top_design.xml"),
            "--lib",
            str(FIXTURES / "basic"),
        ]
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "linked 'example.org:soc:top:1.0'" in out
    assert "no errors" in out


def test_link_with_missing_lib_dir_exits_nonzero(capsys, tmp_path):
    exit_code = main(
        [
            "link",
            str(FIXTURES / "basic" / "top_design.xml"),
            "--lib",
            str(tmp_path / "does_not_exist"),
        ]
    )

    assert exit_code == 1
    assert "library scan root does not exist" in capsys.readouterr().err


def test_link_with_lib_files_only_exits_zero(capsys):
    # the whole file list after a single --lib-file, as a build system gives it.
    basic = FIXTURES / "basic"
    lib_files = [str(path) for path in sorted(basic.glob("*.xml"))]

    exit_code = main(["link", str(basic / "top_design.xml"), "--lib-file", *lib_files])

    assert exit_code == 0
    assert "linked 'example.org:soc:top:1.0' with no errors" in capsys.readouterr().out


def test_link_mixes_lib_and_lib_file(capsys, tmp_path):
    # the design's components come from one folder, its bus definitions from files given by name.
    basic = FIXTURES / "basic"
    for name in ("initiator_component.xml", "target_component.xml"):
        (tmp_path / name).write_bytes((basic / name).read_bytes())

    exit_code = main(
        [
            "link",
            str(basic / "top_design.xml"),
            "--lib",
            str(tmp_path),
            "--lib-file",
            str(basic / "simplebus_busdefinition.xml"),
            "--lib-file=" + str(basic / "simplebus_abstractiondefinition.xml"),
        ]
    )

    assert exit_code == 0, capsys.readouterr().err


def test_link_with_missing_lib_file_exits_nonzero(capsys, tmp_path):
    exit_code = main(
        [
            "link",
            str(FIXTURES / "basic" / "top_design.xml"),
            "--lib-file",
            str(tmp_path / "does_not_exist.xml"),
        ]
    )

    assert exit_code == 1
    assert "library file does not exist" in capsys.readouterr().err


def test_link_reports_unresolvable_component_ref_and_exits_nonzero(capsys):
    exit_code = main(
        [
            "link",
            str(FIXTURES / "cli" / "broken_design.xml"),
            "--lib",
            str(FIXTURES / "basic"),
        ]
    )

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "SCR 1.9" in err


def test_link_does_not_duplicate_diagnostics_when_design_is_also_inside_lib(capsys):
    # Library.scan already single-doc-checks every file it scans, including the top design
    # itself when --lib points at (or includes) the directory it lives in; link() checks
    # the same design again independently. The two diagnostic lists must be deduped when
    # combined, not just concatenated.
    exit_code = main(
        [
            "link",
            str(FIXTURES / "cli" / "duplicate_interface_design.xml"),
            "--lib",
            str(FIXTURES / "cli"),
        ]
    )

    assert exit_code == 1
    err = capsys.readouterr().err
    assert err.count("SCR 2.3") == 2  # one per (instance, bus interface) pair, not doubled


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


def test_a_broken_installed_plugin_does_not_crash_unrelated_commands(monkeypatch, capsys):
    # discover_exporters()/discover_importers() run during _build_parser(), before any
    # subcommand is even chosen, so a plugin that fails to load must not crash commands (like
    # check, used here) that have nothing to do with that plugin.
    class _BrokenEntryPoint:
        name = "broken"

        def load(self):
            raise ImportError("No module named 'xactflow_broken_plugin'")

    monkeypatch.setattr("xactflow.exporter._entry_points_for_group", lambda group: [_BrokenEntryPoint()])

    exit_code = main(["check", str(FIXTURES / "basic" / "top_design.xml")])

    assert exit_code == 0
    assert capsys.readouterr().err == (
        "warning: skipping entry point 'broken' in group 'xactflow.exporters': "
        "failed to load: No module named 'xactflow_broken_plugin'\n"
    )


def test_no_plugin_subcommands_when_none_are_installed(capsys):
    # with no exporters/importers registered (the real state of this repo, which ships none),
    # only the built-in link/check subcommands should exist.
    with pytest.raises(SystemExit):
        main(["fake-exporter", str(FIXTURES / "basic" / "top_design.xml")])
    assert "invalid choice" in capsys.readouterr().err


class _FakeExporter(Exporter):
    name = "fake"
    exported: list = []

    def export(self, library, output_dir, **options):
        type(self).exported.append((library, output_dir, options))


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
    library, output_dir, options = _FakeExporter.exported[0]
    # the design is the only target, though it is also under --lib; the rest is there to look up.
    assert [str(d.vlnv) for d in library.targets()] == ["example.org:soc:top:1.0"]
    assert len(list(library.documents(ipxact.Component))) == 2
    assert output_dir == tmp_path
    assert options == {"flavor": "minimal"}
    assert "exported Design 'example.org:soc:top:1.0' via 'fake-exporter'" in capsys.readouterr().out


def test_installed_exporter_runs_on_a_file_that_is_not_a_design(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("xactflow.cli.discover_exporters", lambda: {"fake-exporter": _FakeExporter})
    _FakeExporter.exported.clear()

    exit_code = main(["fake-exporter", str(FIXTURES / "basic" / "target_component.xml"), "--output", str(tmp_path)])

    assert exit_code == 0
    library, _, _ = _FakeExporter.exported[0]
    assert [str(d.vlnv) for d in library.targets()] == ["example.org:ip:target_comp:1.0"]


def test_installed_exporter_does_not_run_when_linking_has_errors(monkeypatch, tmp_path):
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


def test_installed_exporter_does_not_run_on_a_file_that_is_not_ipxact(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("xactflow.cli.discover_exporters", lambda: {"fake-exporter": _FakeExporter})
    _FakeExporter.exported.clear()

    exit_code = main(["fake-exporter", str(FIXTURES / "not_ipxact" / "not_ipxact.xml"), "--output", str(tmp_path)])

    assert exit_code == 1
    assert _FakeExporter.exported == []
    assert "could not be added to the library" in capsys.readouterr().err


class _FakeImporter(Importer):
    """Adds the component example.org:ip:<source stem>:1.0, and records what it was given."""

    name = "fake"
    imported: list = []

    def import_(self, source_path, library, **options):
        type(self).imported.append((source_path, len(list(library.documents())), options))
        vlnv = ipxact.VLNV.parse(f"example.org:ip:{source_path.stem}:1.0")
        library.add(ipxact.Component(vlnv=vlnv), target=True)


class _EmptyFakeImporter(Importer):
    name = "empty"

    def import_(self, source_path, library, **options):
        pass


def test_installed_importer_becomes_its_own_top_level_subcommand(monkeypatch, capsys):
    monkeypatch.setattr("xactflow.cli.discover_importers", lambda: {"fake-importer": _FakeImporter})
    _FakeImporter.imported.clear()

    exit_code = main(["fake-importer", "generated.sv", "--option", "mode=strict"])

    assert exit_code == 0
    assert _FakeImporter.imported == [(Path("generated.sv"), 0, {"mode": "strict"})]
    out = capsys.readouterr().out
    assert "imported 'generated.sv' via 'fake-importer': Component 'example.org:ip:generated:1.0'" in out


def test_importer_can_look_up_the_documents_scanned_from_lib(monkeypatch):
    monkeypatch.setattr("xactflow.cli.discover_importers", lambda: {"fake-importer": _FakeImporter})
    _FakeImporter.imported.clear()

    exit_code = main(["fake-importer", "generated.sv", "--lib", str(FIXTURES / "basic")])

    assert exit_code == 0
    assert _FakeImporter.imported == [(Path("generated.sv"), 5, {})]


def test_importer_that_adds_no_target_is_an_error(monkeypatch, capsys):
    monkeypatch.setattr("xactflow.cli.discover_importers", lambda: {"empty": _EmptyFakeImporter})

    exit_code = main(["empty", "generated.sv"])

    assert exit_code == 1
    assert "'empty' added no target document to the library" in capsys.readouterr().err


class _ChainableFakeExporter(Exporter):
    name = "chainable"
    calls: list = []

    def export(self, library, output_dir, **options):
        type(self).calls.append((library, output_dir, options))


class _TypeRejectingFakeExporter(Exporter):
    name = "picky"

    def export(self, library, output_dir, **options):
        raise TypeError("picky only supports ipxact.Design targets")


def test_then_hands_the_library_the_importer_added_to_straight_to_an_exporter(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("xactflow.cli.discover_exporters", lambda: {"chainable": _ChainableFakeExporter})
    monkeypatch.setattr("xactflow.cli.discover_importers", lambda: {"fake-importer": _FakeImporter})
    _ChainableFakeExporter.calls.clear()
    _FakeImporter.imported.clear()

    exit_code = main(
        [
            "fake-importer",
            "generated.sv",
            "--lib",
            str(FIXTURES / "basic"),
            "--option",
            "mode=strict",
            "--then",
            "chainable",
            "--output",
            str(tmp_path),
            "--then-option",
            "flavor=minimal",
        ]
    )

    assert exit_code == 0
    assert _FakeImporter.imported == [(Path("generated.sv"), 5, {"mode": "strict"})]
    assert len(_ChainableFakeExporter.calls) == 1
    library, output_dir, options = _ChainableFakeExporter.calls[0]
    # only what the importer added is a target; what --lib scanned is still there to look up.
    assert [str(d.vlnv) for d in library.targets()] == ["example.org:ip:generated:1.0"]
    assert len(list(library.documents(ipxact.Component))) == 3
    assert output_dir == tmp_path
    assert options == {"flavor": "minimal"}
    out = capsys.readouterr().out
    assert "imported" in out
    assert "exported via 'chainable'" in out


def test_then_does_not_export_when_the_import_gives_a_library_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("xactflow.cli.discover_exporters", lambda: {"chainable": _ChainableFakeExporter})
    monkeypatch.setattr("xactflow.cli.discover_importers", lambda: {"fake-importer": _FakeImporter})
    _ChainableFakeExporter.calls.clear()

    # example.org:ip:target_comp:1.0 is already under --lib: an SCR 1.1 duplicate VLNV.
    exit_code = main(
        ["fake-importer", "target_comp.sv", "--lib", str(FIXTURES / "basic"), "--then", "chainable"]
    )

    assert exit_code == 1
    assert _ChainableFakeExporter.calls == []
    err = capsys.readouterr().err
    assert "SCR 1.1" in err
    assert "not exporting: the library reported errors" in err


def test_then_with_unknown_exporter_name_is_an_argparse_error(monkeypatch, capsys):
    monkeypatch.setattr("xactflow.cli.discover_exporters", lambda: {"chainable": _ChainableFakeExporter})
    monkeypatch.setattr("xactflow.cli.discover_importers", lambda: {"fake-importer": _FakeImporter})

    with pytest.raises(SystemExit):
        main(["fake-importer", "generated.sv", "--then", "does-not-exist"])
    assert "invalid choice" in capsys.readouterr().err


def test_then_surfaces_a_clear_error_when_the_exporter_rejects_the_targets(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("xactflow.cli.discover_exporters", lambda: {"picky": _TypeRejectingFakeExporter})
    monkeypatch.setattr("xactflow.cli.discover_importers", lambda: {"fake-importer": _FakeImporter})

    exit_code = main(["fake-importer", "generated.sv", "--then", "picky", "--output", str(tmp_path)])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "'picky' cannot export the output of 'fake-importer'" in err
    assert "Component 'example.org:ip:generated:1.0'" in err  # names what it was given
    assert "Traceback" not in err


class _MisbehavingFakeExporter(Exporter):
    name = "misbehaving"

    def export(self, library, output_dir, **options):
        # a non-compliant exporter that doesn't follow the TypeError-for-rejection convention,
        # e.g. unguarded access to a target kind the library does not hold.
        next(library.targets(ipxact.Design))


def test_then_contextualizes_a_non_type_error_from_the_exporter_too(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("xactflow.cli.discover_exporters", lambda: {"misbehaving": _MisbehavingFakeExporter})
    monkeypatch.setattr("xactflow.cli.discover_importers", lambda: {"fake-importer": _FakeImporter})

    exit_code = main(["fake-importer", "generated.sv", "--then", "misbehaving", "--output", str(tmp_path)])

    assert exit_code == 1
    err = capsys.readouterr().err
    # still names both plugins and the targets, unlike main()'s bare "error: ..." fallback, even
    # though this exporter didn't raise the documented TypeError convention.
    assert "'misbehaving' failed while exporting the output of 'fake-importer'" in err
    assert "Component 'example.org:ip:generated:1.0'" in err
    assert not err.startswith("error: ")
    assert "Traceback" not in err


def test_then_option_without_then_is_a_clear_error(monkeypatch, capsys):
    monkeypatch.setattr("xactflow.cli.discover_exporters", lambda: {})
    monkeypatch.setattr("xactflow.cli.discover_importers", lambda: {"fake-importer": _FakeImporter})

    exit_code = main(["fake-importer", "generated.sv", "--then-option", "flavor=minimal"])

    assert exit_code == 1
    assert "--then-option requires --then" in capsys.readouterr().err


def test_plugin_name_colliding_with_a_builtin_command_is_skipped(monkeypatch, capsys):
    monkeypatch.setattr("xactflow.cli.discover_exporters", lambda: {"check": _FakeExporter})
    monkeypatch.setattr("xactflow.cli.discover_importers", lambda: {})

    # "check" stays the real built-in command, not the fake exporter.
    exit_code = main(["check", str(FIXTURES / "basic" / "top_design.xml")])

    assert exit_code == 0
    assert "conflicts with an existing xactflow subcommand" in capsys.readouterr().err
