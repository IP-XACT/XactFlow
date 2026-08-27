# XactFlow

Multi-file [IEEE 1685-2022](https://standards.ieee.org/ieee/1685/10307/) IP-XACT elaboration
and semantic consistency checking, built on top of
[`ipxact-compiler`](https://github.com/IP-XACT/ipxact-compiler) (a standalone single-file
IP-XACT parser).

`ipxact-compiler` parses one IP-XACT XML document into a Python object model and stops there,
no cross-file resolution, no validation or further checking.
XactFlow is what consumes those parsed objects to do the higher-level work: resolving a
`Design` (and its component instances, bus interfaces, and interconnections) against a library
of `Component`/`BusDefinition`/`AbstractionDefinition` files into one combined, navigable
object graph, and checking that graph against IP-XACT Semantic Consistency Rules (SCRs).

## Installation

```bash
pip install xactflow
```

`ipxact-compiler` is not published to PyPI yet; until it is, install it manually first (e.g.
`pip install -e /path/to/ipxact-compiler`) before installing XactFlow. For local development,
`requirements-dev.txt` assumes `ipxact-compiler` is checked out as a sibling directory:

```bash
pip install -r requirements-dev.txt -e .
```

Requires Python >= 3.9.

## CLI

```bash
xactflow elaborate <design.xml> [--lib DIR ...] [--config <designConfig.xml>]
xactflow check <file.xml>
```

`elaborate` scans every `--lib` directory into a library indexed by VLNV, resolves `<design.xml>`
against it (component instances, bus interfaces, interconnections, monitor interconnections, ad
hoc connections), runs SCR checks on the result, prints every diagnostic, and exits nonzero if
any of them is an error.

`check` runs only the SCR rules that are checkable on a single document (no library needed) and
is useful for validating one file in isolation, e.g. as a pre-commit or CI step.

Installed exporter and importer plugins each become their own top-level subcommand
automatically, named after whatever entry point name they registered under
(`xactflow.exporters` / `xactflow.importers`), e.g. `xactflow html design.xml -o docs/` once a
package like that is installed. XactFlow itself ships no exporters or importers; see
[Plugins](#plugins) below.

## Library usage

```python
import ipxact
from xactflow import Library, elaborate

library = Library.scan("path/to/ip/library")
design = ipxact.parse_file("path/to/top_design.xml")

elaborated = elaborate(design, library)

elaborated.instances          # dict[str, ElaboratedInstance], keyed by instance name
elaborated.interconnections   # list[ElaboratedInterconnection], every endpoint resolved
elaborated.diagnostics        # list[Diagnostic] from every applicable SCR rule
```

## Semantic Consistency Rules (SCR)

IEEE 1685-2022's Annex B defines 281 SCRs across 15 tables, each independently tagged
`single doc check` (checkable on one document alone) and `post config` (only applies once
configuration has been completed). Every one of them is registered in `xactflow.SCR`, one module
per table (`SCR/scr_01.py` through `SCR/scr_15.py`), so the full set is always discoverable:

```python
from xactflow import SCR

len(SCR.all_rules())                                   # 281
[r.id for r in SCR.all_rules() if r.implemented]        # currently implemented: SCR 1.2, 1.9, 2.1-2.5
```

A rule with `implemented=False` is registered (id, name, table, the two flags, and the rule text
as its description) but its check always reports nothing; that's a deliberate placeholder, not a
bug, tracking Annex B's full rule set ahead of writing the check logic for each one. Table B.14
(expressions) and most of the overlap/alignment rules in Tables B.7-B.9 additionally need real
IP-XACT expression evaluation, which neither `ipxact-compiler` nor XactFlow implements yet
(`Expression` fields are unevaluated strings in the object model).

`SCR.run_single_doc_checks(document)` and `SCR.run_post_config_checks(elaborated)` are public,
standalone functions independent of the elaborator's internals, so any caller (including a
future exporter that itself emits IP-XACT) should re-run SCR checking on IP-XACT it produced, not
only on the input.

## Plugins

XactFlow defines two plugin interfaces, both discovered via
[entry points](https://packaging.python.org/en/latest/specifications/entry-points/), neither
implemented in this repository:

- `xactflow.Exporter` (`xactflow.exporters` entry point group): turns some IP-XACT-flavored
  Python object into an output artifact, e.g. RTL, documentation, or another IP-XACT file. Its
  `export(subject, output_dir, **options)` method leaves `subject` deliberately untyped: it may
  be an `ElaboratedDesign` (a fully resolved multi-instance design), a bare `ipxact.Component` or
  `ipxact.Design`, or anything else a given exporter chooses to support.
  Each exporter documents and checks what it actually accepts.
- `xactflow.Importer` (`xactflow.importers` entry point group): reads a non-IP-XACT source (a
  custom design description, an annotated SystemVerilog file, etc.) and produces an IP-XACT
  object model instance from it.

A package that generates IP-XACT itself (from a hand-built object model, or as an importer's
downstream step) is still just an `Exporter` writing its own XML; that capability lives in its
own package rather than in `ipxact-compiler` or XactFlow.

A plugin package registers itself in its own `pyproject.toml`:

```toml
[project.entry-points."xactflow.exporters"]
html = "xactflow_html:HtmlExporter"
```

## Known limitations

- **No IP-XACT expression evaluation.** `addressOffset`, `size`, `range`, `width`, `bitOffset`,
  and similar fields are unevaluated `str` in the object model (`ipxact-compiler`'s deliberate
  choice, carried through here). This blocks most of the overlap/alignment/stride SCRs,
  from having real check logic yet.
- **No multi-level design hierarchy.** `elaborate()` resolves one `Design` flat, it does not
  recurse into a design nested inside another design's hierarchy. It will be supported in the future.
- **No `DesignConfiguration` application.** A `DesignConfiguration` can be passed to `elaborate()`
  and its single-doc rules get checked, but nothing actually applies it yet.
- **Monitor interconnections and ad hoc connections resolve but aren't checked.** `elaborate()`
  resolves both into the graph, but no SCR rule (Table B.4, or the ad hoc rules in B.2/B.6) has
  check logic yet, so a broken monitor or ad hoc reference is silently dropped rather than
  reported.
- **274 of 281 SCR rules have no check logic.** See [Semantic Consistency
  Rules](#semantic-consistency-rules-scr) above. 

## Ideas for later

- Real IP-XACT expression evaluation.
- Multi-level design hierarchy elaboration.
- A better SCR coverage, especially for the single file and pre config ones.
- The actual exporter and importer plugin packages (an elaborated design to RTL exporter, an IP-XACT-emitting
  exporter (component & design), a SystemVerilog-with-metadata importer, etc.), each in its own repository per
  [Plugins](#plugins) above.

## License

LGPL-3.0. See [LICENSE](LICENSE).
