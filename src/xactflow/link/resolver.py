from __future__ import annotations

from typing import Dict, List, Optional

import ipxact

from .. import SCR
from ..diagnostics import Diagnostic, Severity
from ..library import Library
from .model import (
    LinkedDesign,
    LinkedInstance,
    LinkedInterconnection,
    LinkedMonitorInterconnection,
    ResolvedExternalPortReference,
    ResolvedHierInterface,
    ResolvedInterfaceEndpoint,
    ResolvedPortReference,
)


def link(
    design: ipxact.Design,
    library: Library,
    design_configuration: Optional[ipxact.DesignConfiguration] = None,
    component: Optional[ipxact.Component] = None,
) -> LinkedDesign:
    """Resolve a Design (and optional DesignConfiguration) against a Library.

    Every reference that can be resolved is, then the SCRs explain the others: the single-doc
    rules on the design and the design configuration, then the other rules on the linked result.
    The single-doc rules run even if the design came from a Library.scan, which already ran
    them: the design given here is often not in the library, e.g. the file given to the CLI.

    The hierInterface and externalPortReference elements refer to the bus interfaces and ports
    of the component containing the design: `component` if given, otherwise the one component
    of the library with a view instantiating the design (see _instantiates_design). With none,
    or several, they are not resolved, and a warning says so.
    """

    linked = LinkedDesign(
        vlnv=design.vlnv,
        design=design,
        library=library,
        design_configuration=design_configuration,
    )

    _find_containing_component(linked, component)
    _resolve_instances(linked)
    _resolve_interconnections(linked)
    _resolve_monitor_interconnections(linked)
    _resolve_ad_hoc_connections(linked)

    linked.diagnostics.extend(SCR.run_single_doc_checks(design))
    if design_configuration is not None:
        linked.diagnostics.extend(SCR.run_single_doc_checks(design_configuration))
    linked.diagnostics.extend(SCR.run_post_config_checks(linked))

    return linked


def _instantiates_design(component: ipxact.Component, design_vlnv: ipxact.VLNV, library: Library) -> bool:
    """Whether a view of the component instantiates the design: through its designInstantiationRef,
    or, without one, through the designRef of the design configuration its
    designConfigurationInstantiationRef references (see 6.15.1.2 and SCR 1.16).
    """
    model = component.model
    if model is None:
        return False
    design_instantiations = {i.name: i for i in model.design_instantiations}
    configuration_instantiations = {i.name: i for i in model.design_configuration_instantiations}
    for view in model.views:
        if view.design_instantiation_ref is not None:
            instantiation = design_instantiations.get(view.design_instantiation_ref)
            if instantiation is not None and instantiation.design_ref.vlnv == design_vlnv:
                return True
        elif view.design_configuration_instantiation_ref is not None:
            instantiation = configuration_instantiations.get(view.design_configuration_instantiation_ref)
            if instantiation is None:
                continue
            configuration = library.get_design_configuration(instantiation.design_configuration_ref.vlnv)
            if (
                configuration is not None
                and configuration.design_ref is not None
                and configuration.design_ref.vlnv == design_vlnv
            ):
                return True
    return False


def _find_containing_component(linked: LinkedDesign, component: Optional[ipxact.Component]) -> None:
    design = linked.design
    if component is not None:
        if not _instantiates_design(component, linked.vlnv, linked.library):
            linked.diagnostics.append(
                Diagnostic(
                    message=f"component {component.vlnv}, given as the component containing design "
                    f"{linked.vlnv}, has no view instantiating it",
                    severity=Severity.ERROR,
                    location=str(component.vlnv),
                )
            )
        linked.component = component
        return

    candidates = [
        document
        for document in linked.library.documents()
        if isinstance(document, ipxact.Component)
        and _instantiates_design(document, linked.vlnv, linked.library)
    ]
    if len(candidates) == 1:
        linked.component = candidates[0]
        return

    has_external_references = any(i.hier_interfaces for i in design.interconnections) or any(
        a.external_port_references for a in design.ad_hoc_connections
    )
    if not has_external_references:
        return
    if candidates:
        detail = (
            f"several components of the library instantiate it "
            f"({', '.join(str(c.vlnv) for c in candidates)}); pass the one to use to link()"
        )
    else:
        detail = "no component of the library instantiates it"
    linked.diagnostics.append(
        Diagnostic(
            message=f"hierInterface and externalPortReference elements of design {linked.vlnv} are "
            f"not checked: {detail}",
            severity=Severity.WARNING,
            location=str(linked.vlnv),
        )
    )


def _resolve_instances(linked: LinkedDesign) -> None:
    instance_refs: Dict[str, List[ipxact.ComponentInstance]] = {}
    for instance_ref in linked.design.component_instances:
        instance_refs.setdefault(instance_ref.instance_name, []).append(instance_ref)

    for name, (instance_ref, *duplicates) in instance_refs.items():
        if duplicates:
            linked.diagnostics.append(
                Diagnostic(
                    message=f"instanceName '{name}' is used by {1 + len(duplicates)} "
                    f"componentInstance elements",
                    severity=Severity.ERROR,
                    location=f"{linked.vlnv}/{name}",
                )
            )
        component = linked.library.get_component(instance_ref.component_ref.vlnv)
        if component is None:
            continue  # scr.rules._check_component_ref_is_component (SCR 1.9) reports why
        linked.instances[name] = LinkedInstance(
            instance_name=name,
            component=component,
            component_vlnv=instance_ref.component_ref.vlnv,
            source=instance_ref,
        )


def _resolve_bus_interface_endpoint(
    linked: LinkedDesign, component_instance_ref: str, bus_ref: str, source
) -> Optional[ResolvedInterfaceEndpoint]:
    instance = linked.instances.get(component_instance_ref)
    if instance is None:
        return None
    bus_interface = next(
        (bi for bi in instance.component.bus_interfaces if bi.name == bus_ref), None
    )
    if bus_interface is None:
        return None
    return ResolvedInterfaceEndpoint(instance=instance, bus_interface=bus_interface, source=source)


def _resolve_interconnections(linked: LinkedDesign) -> None:
    for interconnection in linked.design.interconnections:
        active_interfaces = [
            interconnection.active_interface,
            *interconnection.other_active_interfaces,
        ]
        # A hierInterface has no componentInstanceRef: None stands for the containing component.
        interfaces = [(ai.component_instance_ref, ai.bus_ref) for ai in active_interfaces] + [
            (None, hi.bus_ref) for hi in interconnection.hier_interfaces
        ]
        for instance_ref, bus_ref in dict.fromkeys(i for i in interfaces if interfaces.count(i) > 1):
            interface = (
                f"hierInterface '{bus_ref}'"
                if instance_ref is None
                else f"component instance '{instance_ref}' bus interface '{bus_ref}'"
            )
            linked.diagnostics.append(
                Diagnostic(
                    message=f"interconnection '{interconnection.name}' connects {interface} to itself",
                    severity=Severity.ERROR,
                    location=f"{linked.vlnv}/{interconnection.name}",
                )
            )
        endpoints = [
            _resolve_bus_interface_endpoint(
                linked, ai.component_instance_ref, ai.bus_ref, ai
            )
            for ai in active_interfaces
        ]
        # Keep whatever endpoints did resolve rather than dropping the whole interconnection:
        # scr.rules._check_active_interfaces_exist (SCR 2.1) reports each one that didn't, but
        # SCR 2.2/2.4/2.5 still need to see the ones that did, e.g. two valid-but-incompatible
        # endpoints alongside a third with an unrelated typo.
        resolved_endpoints = [endpoint for endpoint in endpoints if endpoint is not None]
        linked.interconnections.append(
            LinkedInterconnection(
                name=interconnection.name,
                endpoints=resolved_endpoints,
                hier_interfaces=_resolve_hier_interfaces(linked, interconnection),
                source=interconnection,
            )
        )


def _resolve_hier_interfaces(
    linked: LinkedDesign, interconnection: ipxact.Interconnection
) -> List[ResolvedHierInterface]:
    if linked.component is None:
        return []  # _find_containing_component warned, if there is any hierInterface
    resolved = []
    for hier_interface in interconnection.hier_interfaces:
        bus_interface = next(
            (bi for bi in linked.component.bus_interfaces if bi.name == hier_interface.bus_ref), None
        )
        if bus_interface is None:
            # No Annex B rule covers this: SCR 2.1 is only about activeInterface. See 7.4.2.
            linked.diagnostics.append(
                Diagnostic(
                    message=f"interconnection '{interconnection.name}' hierInterface busRef "
                    f"'{hier_interface.bus_ref}' does not match a busInterface on component "
                    f"{linked.component.vlnv}, which contains the design",
                    severity=Severity.ERROR,
                    location=f"{linked.vlnv}/{interconnection.name}",
                )
            )
            continue
        resolved.append(ResolvedHierInterface(bus_interface=bus_interface, source=hier_interface))
    return resolved


def _resolve_monitor_interconnections(linked: LinkedDesign) -> None:
    # No SCR rule covers monitor interconnections in this first slice (Table B.4 is not yet
    # implemented); resolution here is best-effort so the graph is complete when those rules
    # are added later, but nothing reports why a monitor endpoint failed to resolve yet.
    for monitor_interconnection in linked.design.monitor_interconnections:
        active_ref = monitor_interconnection.monitored_active_interface
        active_endpoint = _resolve_bus_interface_endpoint(
            linked, active_ref.component_instance_ref, active_ref.bus_ref, active_ref
        )
        if active_endpoint is None:
            continue
        monitor_endpoints = [
            _resolve_bus_interface_endpoint(
                linked, ref.component_instance_ref, ref.bus_ref, ref
            )
            for ref in monitor_interconnection.monitor_interfaces
        ]
        if any(endpoint is None for endpoint in monitor_endpoints):
            continue
        linked.monitor_interconnections.append(
            LinkedMonitorInterconnection(
                name=monitor_interconnection.name,
                monitored_active_interface=active_endpoint,
                monitor_interfaces=monitor_endpoints,
                source=monitor_interconnection,
            )
        )


def _resolve_ad_hoc_connections(linked: LinkedDesign) -> None:
    # SCR 13.5 (scr_13._check_ad_hoc_port_refs_exist) reports the references that do not resolve.
    component_ports = {}
    if linked.component is not None and linked.component.model is not None:
        component_ports = {port.name: port for port in linked.component.model.ports}
    for ad_hoc in linked.design.ad_hoc_connections:
        resolved = [
            reference
            for reference in (
                _resolve_internal_port_reference(linked, ref)
                for ref in ad_hoc.internal_port_references
            )
            if reference is not None
        ]
        if resolved:
            linked.ad_hoc_connections[ad_hoc.name] = resolved
        external = [
            ResolvedExternalPortReference(port=component_ports[ref.port_ref], source=ref)
            for ref in ad_hoc.external_port_references
            if ref.port_ref in component_ports
        ]
        if external:
            linked.ad_hoc_external_ports[ad_hoc.name] = external


def _resolve_internal_port_reference(
    linked: LinkedDesign, ref: ipxact.InternalPortReference
) -> Optional[ResolvedPortReference]:
    instance = linked.instances.get(ref.component_instance_ref)
    if instance is None or instance.component.model is None:
        return None
    port = next((p for p in instance.component.model.ports if p.name == ref.port_ref), None)
    if port is None:
        return None
    return ResolvedPortReference(instance=instance, port=port, source=ref)
