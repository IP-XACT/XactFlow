# XactFlow

Multi-file [IEEE 1685-2022](https://standards.ieee.org/ieee/1685/10307/) IP-XACT linking and
checking, built on [`ipxact-compiler`](https://github.com/IP-XACT/ipxact-compiler).

`ipxact-compiler` reads one IP-XACT file into Python objects and can validate it against the
XSD. XactFlow works across files: it resolves a `Design` against a library of components, bus
definitions and abstraction definitions, and checks the result against the Semantic Consistency
Rules (SCRs) of the standard.

## Installation

```bash
pip install xactflow
```

Requires Python 3.9 or later. 

For development, `requirements-dev.txt` installs
`ipxact-compiler` from a sibling checkout (`../ipxact-compiler`); change the path if needed:

```bash
pip install -r requirements-dev.txt -e .
```

## Command line

```bash
xactflow link design.xml --lib DIR [--lib DIR ...] [--config designConfig.xml]
xactflow check file.xml
```

- `link` scans the `--lib` folders, resolves the design against them, prints the diagnostics,
  and exits with 1 if any is an error.
- `check` runs the checks that need only one file, e.g. in CI or a pre-commit hook.

Each installed plugin adds its own subcommand (see [Plugins](#plugins)):

- an exporter: `xactflow <exporter> design.xml --lib DIR --output DIR`, which links the design
  and passes the `LinkedDesign` to the exporter;
- an importer: `xactflow <importer> source --output DIR`, with `--then <exporter>` to pass its
  result straight to an exporter, without an intermediate file:

```bash
xactflow sv module.sv --option metadata=module_ipxact.json --then component --output out/
```

`--option KEY=VALUE` sets a plugin option; `--then-option KEY=VALUE` sets one for the `--then`
exporter. If that exporter does not accept the importer's result, the command prints a one-line
error naming both plugins.

## Python

```python
import ipxact
from xactflow import Library, link

library = Library.scan("path/to/ip/library")
design = ipxact.parse_file("path/to/top_design.xml")
linked = link(design, library)

linked.instances          # dict[str, LinkedInstance], by instance name
linked.interconnections   # list[LinkedInterconnection], with the endpoints that resolved
linked.diagnostics        # list[Diagnostic]
```

`Library` indexes documents by VLNV:

- `Library.scan(*folders)` reads every IEEE 1685-2022 file under the folders. A missing folder
  raises an error; files of another IP-XACT version, or a folder with no 1685-2022 file, give a
  warning in `library.diagnostics`.
- `library.add_file(path)` adds one file, with the same checks.
- `library.add(document, path=None, replace=False)` adds a document that only exists in
  memory, e.g. an importer's result. `path` only records where it came from.

A duplicate VLNV is reported as an SCR 1.1 error, unless `replace=True`.

## Expression evaluation

IP-XACT values such as `addressOffset`, `size` or a parameter value are expressions, kept as
text by `ipxact-compiler`. `xactflow.evaluate()` computes them, following the expression
language of IEEE 1685-2022 Annex E (a subset of SystemVerilog):

```python
from xactflow import evaluate, parameter_resolver

evaluate("2 + 3 * 4")                                       # 14
evaluate("{3{1'b1}}")                                       # 7
evaluate("WIDTH - 1", resolve_parameter=lambda name: "8")   # 7

resolve = parameter_resolver(component.parameters)          # by parameterId
evaluate(register.size, resolve_parameter=resolve)          # an ipxact.Expression
```

- A referenced parameter is cast to its `type` and `sign`: a `byte` with value `200` is `-56`.
- A value outside its `minimum`/`maximum` raises `ExpressionError`, naming the parameter, or
  the `name=` given to `evaluate()`.
- Supported: integral and real values, all non-string operators (with reductions, `->`,
  `<->`, `inside`), casts, concatenation, replication, streaming, bit and part selects,
  `'0`/`'1`, escaped identifiers, `$clog2` and the real math functions (`$ln`, `$pow`, ...).
- Not supported, because `evaluate()` returns one number: strings and `$sformatf`, array
  parameters, and the `$ipxact_*` functions, whose value depends on the design environment.
- Arithmetic works on plain values, without SystemVerilog's context-dependent width rules:
  `4'hF + 4'h1` is `16`.
- Numbers use SystemVerilog syntax only: write `'h1F`, not `0x1F`.

## Semantic Consistency Rules (SCR)

Annex B of the standard defines 281 SCRs in 15 tables. All are registered in `xactflow.SCR`,
one module per table, with their id, name and text. 7 have a check today: SCR 1.2, 1.9 and
2.1 to 2.5. The others are placeholders that report nothing.

```python
from xactflow import SCR

len(SCR.all_rules())                                # 281
[r.id for r in SCR.all_rules() if r.implemented]    # the 7 rules with a check
```

`SCR.run_single_doc_checks(document)` and `SCR.run_post_config_checks(linked)` can be called on
their own, e.g. by an exporter to check the IP-XACT it writes.

## Plugins

Plugins live in their own packages and are found through
[entry points](https://packaging.python.org/en/latest/specifications/entry-points/):

- an `xactflow.Exporter` (group `xactflow.exporters`) writes an output from an object: RTL,
  documentation, IP-XACT XML... Each exporter says which objects it accepts and raises
  `TypeError` for the others.
- an `xactflow.Importer` (group `xactflow.importers`) reads a non-IP-XACT source and returns
  IP-XACT objects.

```toml
[project.entry-points."xactflow.exporters"]
component = "xactflow_component:ComponentExporter"
```

A plugin that fails to load is skipped with a warning; the others keep working.

| Package | Kind | Subcommand | Does |
|---|---|---|---|
| [XactFlow-sv](https://github.com/IP-XACT/XactFlow-sv) | importer | `sv` | SystemVerilog module + metadata → `ipxact.Component` |
| [XactFlow-archidesc](https://github.com/IP-XACT/XactFlow-archidesc) | importer | `archidesc` | architecture description → `ipxact.Design` |
| [XactFlow-component](https://github.com/IP-XACT/XactFlow-component) | exporter | `component` | `ipxact.Component` → component XML |
| [XactFlow-design](https://github.com/IP-XACT/XactFlow-design) | exporter | `design` | `ipxact.Design` → design XML |

The two exporters take an `ipxact.Component` / `ipxact.Design`, not a `LinkedDesign`: use them
from Python or after an importer with `--then`.

## Limitations and plans

- **274 of the 281 SCRs have no check yet.** Next: the single-file rules, and the
  overlap/alignment rules, which can now use `evaluate()`.
- **Monitor and ad hoc connections are not checked.** `link()` resolves them, but a broken
  reference is dropped without a message.
- **Flat-design  only.** `link()` does not go into designs nested in the hierarchy.

## License

LGPL-3.0. See [LICENSE](LICENSE).
