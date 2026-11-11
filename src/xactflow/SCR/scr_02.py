"""IEEE 1685-2022 Annex B, Table B.2: Interconnections (19 rules, SCR 2.1-2.19).

SCR 2.1 through SCR 2.10 and SCR 2.17 are implemented, exercised by link.resolver. Every other
rule in this table is registered via stub() so it is tracked and discoverable through
SCR.all_rules(), with no check logic yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, FrozenSet, Iterator, List, Optional, Set, Tuple

import ipxact

from ..diagnostics import Diagnostic, Severity
from .registry import rule, stub

if TYPE_CHECKING:
    from ..link.model import LinkedDesign, LinkedInstance, LinkedInterconnection


def _active_interfaces(interconnection: ipxact.Interconnection) -> Iterator[ipxact.ActiveInterface]:
    yield interconnection.active_interface
    yield from interconnection.other_active_interfaces


def _find_bus_interface(instance: "LinkedInstance", bus_ref: str):
    return next((bi for bi in instance.component.bus_interfaces if bi.name == bus_ref), None)


@dataclass(frozen=True)
class _End:
    """One resolved interface of an interconnection: an activeInterface, or a hierInterface on the
    boundary of the component containing the design."""

    hierarchical: bool
    bus_interface: ipxact.BusInterface
    label: str


def _ends(interconnection: "LinkedInterconnection") -> List[_End]:
    return [
        _End(False, e.bus_interface, f"{e.instance.instance_name}/{e.bus_interface.name}")
        for e in interconnection.endpoints
    ] + [
        _End(True, h.bus_interface, f"hierInterface '{h.bus_interface.name}'")
        for h in interconnection.hier_interfaces
    ]


def _all_ends_resolved(interconnection: "LinkedInterconnection", ends: List[_End]) -> bool:
    source = interconnection.source
    return len(ends) == 1 + len(source.other_active_interfaces) + len(source.hier_interfaces)


def _unordered_pairs(ends: List[_End]) -> Iterator[Tuple[_End, _End]]:
    for i in range(len(ends)):
        for j in range(i + 1, len(ends)):
            yield ends[i], ends[j]


def _describe(hierarchical: bool, mode: ipxact.InterfaceMode) -> str:
    return f"{'hierarchical' if hierarchical else 'active'} {mode.value}"


def _extends_ancestors(vlnv: ipxact.VLNV, library) -> Set[ipxact.VLNV]:
    ancestors: Set[ipxact.VLNV] = set()
    current = vlnv
    while True:
        bus_definition = library.get_bus_definition(current)
        if bus_definition is None or bus_definition.extends is None:
            break
        current = bus_definition.extends.vlnv
        if current in ancestors:
            break  # a circular extends chain is SCR 1.42's problem, not this rule's
        ancestors.add(current)
    return ancestors


def _bus_definitions_compatible(a: ipxact.VLNV, b: ipxact.VLNV, library) -> bool:
    if a == b:
        return True
    return b in _extends_ancestors(a, library) or a in _extends_ancestors(b, library)


@rule(
    id="SCR 2.1",
    table="B.2",
    name="connectedIntfsMustExist",
    single_doc_check=False,
    post_config=False,
    description=(
        "In the attributes of an activeInterface, monitoredActiveInterface, or "
        "monitorInterface element, the value of the busRef attribute shall be the name of a "
        "busInterface in the component description referenced by the VLNV of the component "
        "instance named in componentInstanceRef and optional path attributes."
    ),
)
def _check_active_interfaces_exist(linked: "LinkedDesign") -> Iterator[Diagnostic]:
    design_instance_names = {instance.instance_name for instance in linked.design.component_instances}
    for interconnection in linked.design.interconnections:
        for active_interface in _active_interfaces(interconnection):
            instance = linked.instances.get(active_interface.component_instance_ref)
            if instance is None:
                if active_interface.component_instance_ref in design_instance_names:
                    continue 
                yield Diagnostic(
                    message=(
                        f"interconnection '{interconnection.name}' activeInterface "
                        f"componentInstanceRef '{active_interface.component_instance_ref}' "
                        f"does not resolve to a component instance"
                    ),
                    severity=Severity.ERROR,
                    location=f"{linked.vlnv}/{interconnection.name}",
                    rule_id="SCR 2.1",
                    rule_name="connectedIntfsMustExist",
                )
                continue
            if _find_bus_interface(instance, active_interface.bus_ref) is None:
                yield Diagnostic(
                    message=(
                        f"interconnection '{interconnection.name}' activeInterface busRef "
                        f"'{active_interface.bus_ref}' does not match a busInterface on "
                        f"component instance '{instance.instance_name}'"
                    ),
                    severity=Severity.ERROR,
                    location=f"{linked.vlnv}/{interconnection.name}",
                    rule_id="SCR 2.1",
                    rule_name="connectedIntfsMustExist",
                )


@rule(
    id="SCR 2.2",
    table="B.2",
    name="connectedIntfsCompat",
    single_doc_check=False,
    post_config=True,
    description=(
        "In the subelements of an interconnection, the bus interfaces referenced by all "
        "activeInterface and hierInterface subelements shall be compatible, i.e., the busType "
        "elements within the busInterface elements shall reference compatible busDefinitions."
    ),
)
def _check_interconnection_bus_compat(linked: "LinkedDesign") -> Iterator[Diagnostic]:
    for interconnection in linked.interconnections:
        for a, b in _unordered_pairs(_ends(interconnection)):
            if not _bus_definitions_compatible(
                a.bus_interface.bus_type.vlnv, b.bus_interface.bus_type.vlnv, linked.library
            ):
                yield Diagnostic(
                    message=(
                        f"interconnection '{interconnection.name}' connects incompatible bus "
                        f"definitions: {a.label} ({a.bus_interface.bus_type.vlnv}) and "
                        f"{b.label} ({b.bus_interface.bus_type.vlnv})"
                    ),
                    severity=Severity.ERROR,
                    location=f"{linked.vlnv}/{interconnection.name}",
                    rule_id="SCR 2.2",
                    rule_name="connectedIntfsCompat",
                )


@rule(
    id="SCR 2.3",
    table="B.2",
    name="intfConnectedOnlyOnce",
    single_doc_check=True,
    post_config=True,
    description=(
        "A particular component/bus interface combination shall appear in only one "
        "interconnection element in a design."
    ),
)
def _check_interface_connected_once(document: object) -> Iterator[Diagnostic]:
    if not isinstance(document, ipxact.Design):
        return
    # A hierInterface references a bus interface of the component containing the design: None
    # stands for that component.
    seen: Dict[Tuple[Optional[str], str], Dict[str, None]] = {}
    for interconnection in document.interconnections:
        for active_interface in _active_interfaces(interconnection):
            key = (active_interface.component_instance_ref, active_interface.bus_ref)
            seen.setdefault(key, {})[interconnection.name] = None
        for hier_interface in interconnection.hier_interfaces:
            seen.setdefault((None, hier_interface.bus_ref), {})[interconnection.name] = None
    for (instance_ref, bus_ref), interconnection_names in seen.items():
        if len(interconnection_names) > 1:
            if instance_ref is None:
                interface, location = f"hierInterface '{bus_ref}'", f"{document.vlnv}/{bus_ref}"
            else:
                interface = f"component instance '{instance_ref}' bus interface '{bus_ref}'"
                location = f"{document.vlnv}/{instance_ref}/{bus_ref}"
            yield Diagnostic(
                message=(
                    f"{interface} appears in more than one interconnection: "
                    f"{', '.join(interconnection_names)}"
                ),
                severity=Severity.ERROR,
                location=location,
                rule_id="SCR 2.3",
                rule_name="intfConnectedOnlyOnce",
            )


_Connection = Tuple[bool, ipxact.InterfaceMode]  # (hierarchical, mode)

_M = ipxact.InterfaceMode
_ACTIVE, _HIER = False, True


def _check_connects_only_to(
    linked: "LinkedDesign",
    rule_id: str,
    rule_name: str,
    connection: _Connection,
    allowed: FrozenSet[_Connection],
) -> Iterator[Diagnostic]:
    """Report every pair of an interconnection where one end is `connection` and the other is not
    in `allowed`, once per pair."""
    hierarchical, mode = connection
    allowed_text = " or ".join(_describe(*c) for c in sorted(allowed, key=lambda c: (c[0], c[1].value)))
    for interconnection in linked.interconnections:
        for a, b in _unordered_pairs(_ends(interconnection)):
            for end, other in ((a, b), (b, a)):
                if (end.hierarchical, end.bus_interface.mode) != connection:
                    continue
                if (other.hierarchical, other.bus_interface.mode) in allowed:
                    continue
                yield Diagnostic(
                    message=(
                        f"interconnection '{interconnection.name}' connects {end.label} "
                        f"({_describe(end.hierarchical, end.bus_interface.mode)}) to {other.label} "
                        f"({_describe(other.hierarchical, other.bus_interface.mode)}), but an "
                        f"{_describe(hierarchical, mode)} interface may only connect to "
                        f"{allowed_text} interfaces"
                    ),
                    severity=Severity.ERROR,
                    location=f"{linked.vlnv}/{interconnection.name}",
                    rule_id=rule_id,
                    rule_name=rule_name,
                )
                break


@rule(
    id="SCR 2.4",
    table="B.2",
    name="activeMstConnect",
    single_doc_check=False,
    post_config=False,
    description=(
        "An active interface of type initiator shall connect only to active interfaces of type "
        "target or mirrored-initiator or hierarchical interfaces of type initiator."
    ),
)
def _check_active_initiator_connects(linked: "LinkedDesign") -> Iterator[Diagnostic]:
    return _check_connects_only_to(
        linked,
        "SCR 2.4",
        "activeMstConnect",
        (_ACTIVE, _M.INITIATOR),
        frozenset({(_ACTIVE, _M.TARGET), (_ACTIVE, _M.MIRRORED_INITIATOR), (_HIER, _M.INITIATOR)}),
    )


@rule(
    id="SCR 2.5",
    table="B.2",
    name="activeMSlvConnect",
    single_doc_check=False,
    post_config=False,
    description=(
        "An active interface of type mirrored-target shall connect only to active interfaces "
        "of type target or hierarchical interfaces of type mirrored-target."
    ),
)
def _check_active_mirrored_target_connects(linked: "LinkedDesign") -> Iterator[Diagnostic]:
    return _check_connects_only_to(
        linked,
        "SCR 2.5",
        "activeMSlvConnect",
        (_ACTIVE, _M.MIRRORED_TARGET),
        frozenset({(_ACTIVE, _M.TARGET), (_HIER, _M.MIRRORED_TARGET)}),
    )


@rule(
    id="SCR 2.6",
    table="B.2",
    name="hierSlvConnect",
    single_doc_check=False,
    post_config=False,
    description=(
        "A hierarchical interface of type target shall connect only to active interfaces of "
        "type target."
    ),
)
def _check_hier_target_connects(linked: "LinkedDesign") -> Iterator[Diagnostic]:
    return _check_connects_only_to(
        linked, "SCR 2.6", "hierSlvConnect", (_HIER, _M.TARGET), frozenset({(_ACTIVE, _M.TARGET)})
    )


@rule(
    id="SCR 2.7",
    table="B.2",
    name="hierMMstConnect",
    single_doc_check=False,
    post_config=False,
    description=(
        "A hierarchical interface of type mirrored-initiator shall connect only to active "
        "interfaces of type mirrored-initiator."
    ),
)
def _check_hier_mirrored_initiator_connects(linked: "LinkedDesign") -> Iterator[Diagnostic]:
    return _check_connects_only_to(
        linked,
        "SCR 2.7",
        "hierMMstConnect",
        (_HIER, _M.MIRRORED_INITIATOR),
        frozenset({(_ACTIVE, _M.MIRRORED_INITIATOR)}),
    )


@rule(
    id="SCR 2.8",
    table="B.2",
    name="systemConnect",
    single_doc_check=False,
    post_config=True,
    description=(
        "An active interface of type system shall connect only to active interfaces of type "
        "mirrored-system or hierarchical interfaces of type system."
    ),
)
def _check_active_system_connects(linked: "LinkedDesign") -> Iterator[Diagnostic]:
    return _check_connects_only_to(
        linked,
        "SCR 2.8",
        "systemConnect",
        (_ACTIVE, _M.SYSTEM),
        frozenset({(_ACTIVE, _M.MIRRORED_SYSTEM), (_HIER, _M.SYSTEM)}),
    )


@rule(
    id="SCR 2.9",
    table="B.2",
    name="MstSystemConnect",
    single_doc_check=False,
    post_config=True,
    description=(
        "An active interface of type mirrored-system shall connect only to active interfaces "
        "of type system or hierarchical interfaces of type mirrored-system."
    ),
)
def _check_active_mirrored_system_connects(linked: "LinkedDesign") -> Iterator[Diagnostic]:
    return _check_connects_only_to(
        linked,
        "SCR 2.9",
        "MstSystemConnect",
        (_ACTIVE, _M.MIRRORED_SYSTEM),
        frozenset({(_ACTIVE, _M.SYSTEM), (_HIER, _M.MIRRORED_SYSTEM)}),
    )


_DRIVERS: FrozenSet[_Connection] = frozenset(
    {(_ACTIVE, _M.INITIATOR), (_ACTIVE, _M.MIRRORED_TARGET), (_HIER, _M.TARGET), (_HIER, _M.MIRRORED_INITIATOR)}
)


@rule(
    id="SCR 2.10",
    table="B.2",
    name="interconnectionDriver",
    single_doc_check=False,
    post_config=True,
    description=(
        "An interconnection element without system interfaces or mirrored-system interfaces "
        "shall contain one driving interface, which is an active interface referencing an "
        "initiator, a mirrored-target, or a hierarchical interface referencing a target or "
        "mirrored-initiator."
    ),
)
def _check_interconnection_driver(linked: "LinkedDesign") -> Iterator[Diagnostic]:
    for interconnection in linked.interconnections:
        ends = _ends(interconnection)
        if not _all_ends_resolved(interconnection, ends):
            continue  # an interface that did not resolve may be the driver
        if any(e.bus_interface.mode in (_M.SYSTEM, _M.MIRRORED_SYSTEM) for e in ends):
            continue
        drivers = [e for e in ends if (e.hierarchical, e.bus_interface.mode) in _DRIVERS]
        if len(drivers) == 1:
            continue
        found = ", ".join(e.label for e in drivers) if drivers else "none"
        yield Diagnostic(
            message=(
                f"interconnection '{interconnection.name}' has {len(drivers)} driving interfaces "
                f"({found}), but needs exactly one: an active initiator or mirroredTarget, or a "
                f"hierarchical target or mirroredInitiator"
            ),
            severity=Severity.ERROR,
            location=f"{linked.vlnv}/{interconnection.name}",
            rule_id="SCR 2.10",
            rule_name="interconnectionDriver",
        )


stub(
    id="SCR 2.11",
    table="B.2",
    name="MstToSlvBitsLAUMatch",
    single_doc_check=False,
    post_config=False,
    description=(
        "In a direct initiator-to target connection, the value of bitsInLAU in the initiator’s "
        "bus interface shall match the value of bitsInLAU in the target’s bus interface."
    ),
)

stub(
    id="SCR 2.12",
    table="B.2",
    name="MstToSlvIsDirectConnect",
    single_doc_check=False,
    post_config=False,
    description=(
        "In a direct initiator-to-target connection, the bus-Definitions referenced by the "
        "busInterfaces shall have a directConnection element with the value true."
    ),
)

stub(
    id="SCR 2.13",
    table="B.2",
    name="SysToMSysGroupsMatch",
    single_doc_check=False,
    post_config=False,
    description=(
        "In a connection between a system interface and a mirrored-system interface, the "
        "values of the group elements of the two bus interfaces shall be identical."
    ),
)

stub(
    id="SCR 2.14",
    table="B.2",
    name="EndianessMustMatch",
    single_doc_check=False,
    post_config=False,
    description=(
        "The endianess in all bus interfaces shall match for any interconnection using an "
        "addressable bus. If the endianess is not specified at either bus interface, it is "
        "presumed to be little endian."
    ),
)

stub(
    id="SCR 2.15",
    table="B.2",
    name="ConnectionRequired",
    single_doc_check=False,
    post_config=False,
    description=(
        "If a design contains a component with a busInterface that has a "
        "connectionRequired element with the value true, that busInterface shall be included "
        "in an interconnection of the design."
    ),
)

stub(
    id="SCR 2.16",
    table="B.2",
    name="MonIntfPathMustExist",
    single_doc_check=False,
    post_config=True,
    description=(
        "A monitorInterconnection with interfaces that contain a path attribute with a "
        "componetInstanceRef and busRef shall exist in all hierarchical views."
    ),
)

@rule(
    id="SCR 2.17",
    table="B.2",
    name="broadcastConstraint",
    single_doc_check=True,
    post_config=True,
    description=(
        "An interconnection may not contain more than two total activeInterface and "
        "hierInterface elements unless the underlying bus definition has the broadcast "
        "element set to true."
    ),
)
def _check_broadcast(subject: object) -> Iterator[Diagnostic]:
    """Checked on the linked design only: the design alone does not say whether the bus
    definition allows broadcast."""
    from ..link.model import LinkedDesign  # not at the top: xactflow.link imports xactflow.SCR

    if not isinstance(subject, LinkedDesign):
        return
    for interconnection in subject.interconnections:
        source = interconnection.source
        count = 1 + len(source.other_active_interfaces) + len(source.hier_interfaces)
        if count <= 2:
            continue
        bus_types = dict.fromkeys(e.bus_interface.bus_type.vlnv for e in _ends(interconnection))
        not_broadcast = [
            str(vlnv)
            for vlnv in bus_types
            if (definition := subject.library.get_bus_definition(vlnv)) is not None and not definition.broadcast
        ]
        if not_broadcast:
            yield Diagnostic(
                message=(
                    f"interconnection '{interconnection.name}' has {count} activeInterface and "
                    f"hierInterface elements, but bus definition {', '.join(not_broadcast)} does "
                    f"not set broadcast to true"
                ),
                severity=Severity.ERROR,
                location=f"{subject.vlnv}/{interconnection.name}",
                rule_id="SCR 2.17",
                rule_name="broadcastConstraint",
            )

stub(
    id="SCR 2.18",
    table="B.2",
    name="excludePortExists",
    single_doc_check=False,
    post_config=False,
    description=(
        "A physical port name referenced in an excludePort element shall match the name of a "
        "port defined in the ports list of the component."
    ),
)

stub(
    id="SCR 2.19",
    table="B.2",
    name="physicalPortExists",
    single_doc_check=True,
    post_config=False,
    description=(
        "The component abstractionType viewRef elements shall reference views such that all "
        "component ports referenced by physicalPort elements exist."
    ),
)
