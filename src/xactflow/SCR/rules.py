"""First slice of IEEE 1685-2022 Annex B semantic consistency rules.

Covers a working vertical slice: VLNV resolution (Table B.1) and interconnections
(Table B.2), enough to exercise both scr.runner hooks end to end from elaborate.resolver.
The remaining ~120 Annex B rules are additions to this module (or sibling modules split by
table, once this one grows large), following the same @rule pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Iterator, List, Set, Tuple

import ipxact

from ..diagnostics import Diagnostic, Severity
from .registry import rule

if TYPE_CHECKING:
    from ..elaborate.model import ElaboratedDesign, ElaboratedInstance, ElaboratedInterconnection, ResolvedInterfaceEndpoint


def _active_interfaces(interconnection: ipxact.Interconnection) -> Iterator[ipxact.ActiveInterface]:
    yield interconnection.active_interface
    yield from interconnection.other_active_interfaces


def _find_bus_interface(instance: "ElaboratedInstance", bus_ref: str):
    return next((bi for bi in instance.component.bus_interfaces if bi.name == bus_ref), None)


def _unordered_endpoint_pairs(
    interconnection: "ElaboratedInterconnection",
) -> Iterator[Tuple["ResolvedInterfaceEndpoint", "ResolvedInterfaceEndpoint"]]:
    endpoints = interconnection.endpoints
    for i in range(len(endpoints)):
        for j in range(i + 1, len(endpoints)):
            yield endpoints[i], endpoints[j]


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
    id="SCR 1.9",
    table="B.1",
    name="compRefVLNVisComp",
    single_doc_check=False,
    post_config=False,
    description=(
        "The VLNV in a componentInstanceRef element in a design shall be a reference to a "
        "component."
    ),
)
def _check_component_ref_is_component(elaborated: "ElaboratedDesign") -> Iterator[Diagnostic]:
    for instance_ref in elaborated.design.component_instances:
        if instance_ref.instance_name in elaborated.instances:
            continue
        vlnv = instance_ref.component_ref.vlnv
        existing = elaborated.library.get(vlnv)
        if existing is None:
            detail = f"no document with VLNV {vlnv} was found in the library"
        else:
            detail = f"VLNV {vlnv} resolves to a {type(existing).__name__}, not a component"
        yield Diagnostic(
            message=(
                f"componentInstance '{instance_ref.instance_name}' componentRef does not "
                f"resolve to a component: {detail}"
            ),
            severity=Severity.ERROR,
            location=f"{elaborated.vlnv}/{instance_ref.instance_name}",
            rule_id="SCR 1.9",
            rule_name="compRefVLNVisComp",
        )


@rule(
    id="SCR 1.2",
    table="B.1",
    name="anyVLNVRefMustExist",
    single_doc_check=False,
    post_config=False,
    description=(
        "Any VLNV in an IP-XACT document used to reference another IP-XACT document shall "
        "precisely match the identifying VLNV of an existing IP-XACT document. Checked here "
        "for the busType and abstractionRef of every resolved instance's bus interfaces."
    ),
)
def _check_bus_interface_vlnv_refs_exist(elaborated: "ElaboratedDesign") -> Iterator[Diagnostic]:
    for instance in elaborated.instances.values():
        for bus_interface in instance.component.bus_interfaces:
            bus_vlnv = bus_interface.bus_type.vlnv
            if elaborated.library.get_bus_definition(bus_vlnv) is None:
                yield Diagnostic(
                    message=(
                        f"busInterface '{bus_interface.name}' busType references VLNV "
                        f"{bus_vlnv}, which does not resolve to a busDefinition in the library"
                    ),
                    severity=Severity.ERROR,
                    location=f"{instance.instance_name}/{bus_interface.name}",
                    rule_id="SCR 1.2",
                    rule_name="anyVLNVRefMustExist",
                )
            for abstraction_type in bus_interface.abstraction_types:
                abstraction_vlnv = abstraction_type.abstraction_ref.vlnv
                if elaborated.library.get_abstraction_definition(abstraction_vlnv) is None:
                    yield Diagnostic(
                        message=(
                            f"busInterface '{bus_interface.name}' abstractionRef references "
                            f"VLNV {abstraction_vlnv}, which does not resolve to an "
                            f"abstractionDefinition in the library"
                        ),
                        severity=Severity.ERROR,
                        location=f"{instance.instance_name}/{bus_interface.name}",
                        rule_id="SCR 1.2",
                        rule_name="anyVLNVRefMustExist",
                    )


@rule(
    id="SCR 2.1",
    table="B.2",
    name="connectedIntfsMustExist",
    single_doc_check=False,
    post_config=False,
    description=(
        "In the attributes of an activeInterface element, the value of the busRef attribute "
        "shall be the name of a busInterface in the component description referenced by the "
        "VLNV of the component instance named in componentInstanceRef."
    ),
)
def _check_active_interfaces_exist(elaborated: "ElaboratedDesign") -> Iterator[Diagnostic]:
    for interconnection in elaborated.design.interconnections:
        for active_interface in _active_interfaces(interconnection):
            instance = elaborated.instances.get(active_interface.component_instance_ref)
            if instance is None:
                yield Diagnostic(
                    message=(
                        f"interconnection '{interconnection.name}' activeInterface "
                        f"componentInstanceRef '{active_interface.component_instance_ref}' "
                        f"does not resolve to a component instance"
                    ),
                    severity=Severity.ERROR,
                    location=f"{elaborated.vlnv}/{interconnection.name}",
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
                    location=f"{elaborated.vlnv}/{interconnection.name}",
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
        "activeInterface and hierInterface subelements shall be compatible, i.e. the busType "
        "elements within the busInterface elements shall reference compatible busDefinitions."
    ),
)
def _check_interconnection_bus_compat(elaborated: "ElaboratedDesign") -> Iterator[Diagnostic]:
    for interconnection in elaborated.interconnections:
        for a, b in _unordered_endpoint_pairs(interconnection):
            if not _bus_definitions_compatible(
                a.bus_interface.bus_type.vlnv, b.bus_interface.bus_type.vlnv, elaborated.library
            ):
                yield Diagnostic(
                    message=(
                        f"interconnection '{interconnection.name}' connects incompatible bus "
                        f"definitions: {a.instance.instance_name}/{a.bus_interface.name} "
                        f"({a.bus_interface.bus_type.vlnv}) and "
                        f"{b.instance.instance_name}/{b.bus_interface.name} "
                        f"({b.bus_interface.bus_type.vlnv})"
                    ),
                    severity=Severity.ERROR,
                    location=f"{elaborated.vlnv}/{interconnection.name}",
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
    seen: Dict[Tuple[str, str], List[str]] = {}
    for interconnection in document.interconnections:
        for active_interface in _active_interfaces(interconnection):
            key = (active_interface.component_instance_ref, active_interface.bus_ref)
            seen.setdefault(key, []).append(interconnection.name)
    for (instance_ref, bus_ref), interconnection_names in seen.items():
        if len(interconnection_names) > 1:
            yield Diagnostic(
                message=(
                    f"component instance '{instance_ref}' bus interface '{bus_ref}' appears "
                    f"in more than one interconnection: {', '.join(interconnection_names)}"
                ),
                severity=Severity.ERROR,
                location=f"{document.vlnv}/{instance_ref}/{bus_ref}",
                rule_id="SCR 2.3",
                rule_name="intfConnectedOnlyOnce",
            )


@rule(
    id="SCR 2.4",
    table="B.2",
    name="activeMstConnect",
    single_doc_check=False,
    post_config=False,
    description=(
        "An active interface of type initiator shall connect only to active interfaces of "
        "type target or mirrored-initiator, or hierarchical interfaces of type initiator."
    ),
)
def _check_active_initiator_connects(elaborated: "ElaboratedDesign") -> Iterator[Diagnostic]:
    allowed = {ipxact.InterfaceMode.TARGET, ipxact.InterfaceMode.MIRRORED_INITIATOR}
    for interconnection in elaborated.interconnections:
        for a, b in _unordered_endpoint_pairs(interconnection):
            a_mode, b_mode = a.bus_interface.mode, b.bus_interface.mode
            violated = (a_mode is ipxact.InterfaceMode.INITIATOR and b_mode not in allowed) or (
                b_mode is ipxact.InterfaceMode.INITIATOR and a_mode not in allowed
            )
            if violated:
                yield Diagnostic(
                    message=(
                        f"interconnection '{interconnection.name}' connects "
                        f"{a.instance.instance_name}/{a.bus_interface.name} (mode "
                        f"'{a_mode.value}') to {b.instance.instance_name}/{b.bus_interface.name} "
                        f"(mode '{b_mode.value}'), but an initiator interface may only connect "
                        f"to target or mirroredInitiator interfaces"
                    ),
                    severity=Severity.ERROR,
                    location=f"{elaborated.vlnv}/{interconnection.name}",
                    rule_id="SCR 2.4",
                    rule_name="activeMstConnect",
                )


@rule(
    id="SCR 2.5",
    table="B.2",
    name="activeMslvConnect",
    single_doc_check=False,
    post_config=False,
    description=(
        "An active interface of type mirrored-target shall connect only to active interfaces "
        "of type target, or hierarchical interfaces of type mirrored-target."
    ),
)
def _check_active_mirrored_target_connects(
    elaborated: "ElaboratedDesign",
) -> Iterator[Diagnostic]:
    for interconnection in elaborated.interconnections:
        for a, b in _unordered_endpoint_pairs(interconnection):
            a_mode, b_mode = a.bus_interface.mode, b.bus_interface.mode
            violated = (
                a_mode is ipxact.InterfaceMode.MIRRORED_TARGET
                and b_mode is not ipxact.InterfaceMode.TARGET
            ) or (
                b_mode is ipxact.InterfaceMode.MIRRORED_TARGET
                and a_mode is not ipxact.InterfaceMode.TARGET
            )
            if violated:
                yield Diagnostic(
                    message=(
                        f"interconnection '{interconnection.name}' connects "
                        f"{a.instance.instance_name}/{a.bus_interface.name} (mode "
                        f"'{a_mode.value}') to {b.instance.instance_name}/{b.bus_interface.name} "
                        f"(mode '{b_mode.value}'), but a mirrored-target interface may only "
                        f"connect to target interfaces"
                    ),
                    severity=Severity.ERROR,
                    location=f"{elaborated.vlnv}/{interconnection.name}",
                    rule_id="SCR 2.5",
                    rule_name="activeMslvConnect",
                )
