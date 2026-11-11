"""Tests for the references of a design to the component containing it: hierInterface and
externalPortReference, and the SCRs about them (1.5, 2.2-2.10, 2.17, 13.5).
"""

from pathlib import Path

import ipxact

from xactflow import SCR
from xactflow.diagnostics import Severity
from xactflow.library import Library, LibraryEntry
from xactflow.link import link

M = ipxact.InterfaceMode

BUS_A = ipxact.VLNV("example.org", "bus", "bus_a", "1.0")
BUS_B = ipxact.VLNV("example.org", "bus", "bus_b", "1.0")  # unrelated to BUS_A
BUS_BROADCAST = ipxact.VLNV("example.org", "bus", "bus_broadcast", "1.0")
TOP = ipxact.VLNV("example.org", "soc", "top", "1.0")
TOP_DESIGN = ipxact.VLNV("example.org", "soc", "top_design", "1.0")


def _vlnv_ref(vlnv):
    return ipxact.VLNVRef(vlnv.vendor, vlnv.library, vlnv.name, vlnv.version)


def _bus_definition(vlnv, broadcast=None):
    return ipxact.BusDefinition(vlnv=vlnv, direct_connection=True, is_addressable=False, broadcast=broadcast)


def _bus_interface(name, mode, bus_type=BUS_A):
    return ipxact.BusInterface(name=name, bus_type=_vlnv_ref(bus_type), mode=mode)


def _port(name):
    return ipxact.Port(name=name, wire=ipxact.WirePort(direction=ipxact.Direction.IN))


def _component(name, *bus_interfaces, ports=(), design=None):
    """A component; with design, a top-level one whose 'rtl' view instantiates that design."""
    model = ipxact.Model(ports=list(ports))
    if design is not None:
        model.design_instantiations = [ipxact.DesignInstantiation(name="rtl_design", design_ref=_vlnv_ref(design))]
        model.views = [ipxact.View(name="rtl", design_instantiation_ref="rtl_design")]
    return ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", name, "1.0"), bus_interfaces=list(bus_interfaces), model=model
    )


def _instance(name, component):
    return ipxact.ComponentInstance(instance_name=name, component_ref=_vlnv_ref(component.vlnv))


def _interconnection(name, *interfaces):
    """interfaces: (instance name, busRef) for an activeInterface, or a bare busRef for a hierInterface."""
    active = [ipxact.ActiveInterface(component_instance_ref=i, bus_ref=b) for i, b in (x for x in interfaces if isinstance(x, tuple))]
    hier = [ipxact.HierInterface(bus_ref=x) for x in interfaces if isinstance(x, str)]
    return ipxact.Interconnection(
        name=name, active_interface=active[0], other_active_interfaces=active[1:], hier_interfaces=hier
    )


def _design(instances, interconnections=(), ad_hoc_connections=(), vlnv=TOP_DESIGN):
    return ipxact.Design(
        vlnv=vlnv,
        component_instances=list(instances),
        interconnections=list(interconnections),
        ad_hoc_connections=list(ad_hoc_connections),
    )


def _make_library(*documents):
    library = Library()
    for document in documents:
        library.entries[document.vlnv] = LibraryEntry(path=Path(f"<test:{document.vlnv}>"), document=document)
    return library


def _rule(linked, rule_id):
    return [d for d in linked.diagnostics if d.rule_id == rule_id]


def _link_hier(top_mode, active_mode, top_bus=BUS_A):
    """A design connecting one instance's 'bif' (active_mode) to the top's 'bif' (top_mode)."""
    sub = _component("sub", _bus_interface("bif", active_mode))
    top = _component("top", _bus_interface("bif", top_mode, top_bus), design=TOP_DESIGN)
    design = _design([_instance("s0", sub)], [_interconnection("conn0", ("s0", "bif"), "bif")])
    return link(design, _make_library(_bus_definition(BUS_A), _bus_definition(BUS_B), sub, top))


def test_link_resolves_hier_interfaces_and_external_ports_against_the_component_found_in_the_library():
    sub = _component("sub", _bus_interface("m", M.INITIATOR), ports=[_port("clk")])
    top = _component("top", _bus_interface("m", M.INITIATOR), ports=[_port("clk_in")], design=TOP_DESIGN)
    design = _design(
        [_instance("s0", sub)],
        [_interconnection("conn0", ("s0", "m"), "m")],
        [
            ipxact.AdHocConnection(
                name="clk_net",
                internal_port_references=[ipxact.InternalPortReference(component_instance_ref="s0", port_ref="clk")],
                external_port_references=[ipxact.ExternalPortReference(port_ref="clk_in")],
            )
        ],
    )

    linked = link(design, _make_library(_bus_definition(BUS_A), sub, top))

    assert linked.diagnostics == []
    assert linked.component is top
    [hier] = linked.interconnections[0].hier_interfaces
    assert hier.bus_interface is top.bus_interfaces[0]
    assert [r.port.name for r in linked.ad_hoc_external_ports["clk_net"]] == ["clk_in"]


def test_link_uses_the_component_it_is_given_even_if_not_in_the_library():
    sub = _component("sub", _bus_interface("m", M.INITIATOR))
    top = _component("top", _bus_interface("m", M.INITIATOR), design=TOP_DESIGN)
    design = _design([_instance("s0", sub)], [_interconnection("conn0", ("s0", "m"), "m")])

    linked = link(design, _make_library(_bus_definition(BUS_A), sub), component=top)

    assert linked.diagnostics == []
    assert linked.component is top


def test_a_component_given_to_link_that_does_not_instantiate_the_design_is_an_error():
    other = _component("other", design=ipxact.VLNV("example.org", "soc", "other_design", "1.0"))

    linked = link(_design([]), _make_library(), component=other)

    assert [d.message for d in linked.diagnostics if d.rule_id is None] == [
        "component example.org:ip:other:1.0, given as the component containing design "
        "example.org:soc:top_design:1.0, has no view instantiating it"
    ]


def test_the_containing_component_is_found_through_a_design_configuration_instantiation():
    configuration = ipxact.DesignConfiguration(
        vlnv=ipxact.VLNV("example.org", "soc", "top_cfg", "1.0"), design_ref=_vlnv_ref(TOP_DESIGN)
    )
    top = _component("top", _bus_interface("m", M.INITIATOR))
    top.model.design_configuration_instantiations = [
        ipxact.DesignConfigurationInstantiation(name="rtl_cfg", design_configuration_ref=_vlnv_ref(configuration.vlnv))
    ]
    top.model.views = [ipxact.View(name="rtl", design_configuration_instantiation_ref="rtl_cfg")]

    linked = link(_design([]), _make_library(configuration, top))

    assert linked.component is top


def test_hier_references_without_a_containing_component_are_a_warning_and_not_resolved():
    sub = _component("sub", _bus_interface("m", M.INITIATOR))
    design = _design([_instance("s0", sub)], [_interconnection("conn0", ("s0", "m"), "m")])

    linked = link(design, _make_library(_bus_definition(BUS_A), sub))

    assert [(d.severity, d.message) for d in linked.diagnostics] == [
        (
            Severity.WARNING,
            "hierInterface and externalPortReference elements of design example.org:soc:top_design:1.0 "
            "are not checked: no component of the library instantiates it",
        )
    ]
    assert linked.interconnections[0].hier_interfaces == []


def test_several_containing_components_are_a_warning_naming_them():
    sub = _component("sub", _bus_interface("m", M.INITIATOR))
    top1 = _component("top1", _bus_interface("m", M.INITIATOR), design=TOP_DESIGN)
    top2 = _component("top2", _bus_interface("m", M.INITIATOR), design=TOP_DESIGN)
    design = _design([_instance("s0", sub)], [_interconnection("conn0", ("s0", "m"), "m")])

    linked = link(design, _make_library(_bus_definition(BUS_A), sub, top1, top2))

    assert linked.component is None
    [warning] = linked.diagnostics
    assert warning.severity is Severity.WARNING
    assert "example.org:ip:top1:1.0, example.org:ip:top2:1.0" in warning.message


def test_a_hier_interface_bus_ref_missing_from_the_containing_component_is_an_error():
    sub = _component("sub", _bus_interface("m", M.INITIATOR))
    top = _component("top", design=TOP_DESIGN)
    design = _design([_instance("s0", sub)], [_interconnection("conn0", ("s0", "m"), "typo")])

    linked = link(design, _make_library(_bus_definition(BUS_A), sub, top))

    assert [d.message for d in linked.diagnostics if d.rule_id is None] == [
        "interconnection 'conn0' hierInterface busRef 'typo' does not match a busInterface on component "
        "example.org:ip:top:1.0, which contains the design"
    ]


def test_scr_2_2_compares_active_and_hier_interfaces():
    linked = _link_hier(M.INITIATOR, M.INITIATOR, top_bus=BUS_B)

    [diagnostic] = _rule(linked, "SCR 2.2")
    assert "s0/bif (example.org:bus:bus_a:1.0) and hierInterface 'bif' (example.org:bus:bus_b:1.0)" in diagnostic.message


def test_valid_hierarchical_connections_have_no_diagnostics():
    # active initiator - hier initiator, active mirroredTarget - hier mirroredTarget,
    # hier target - active target, hier mirroredInitiator - active mirroredInitiator,
    # active system - hier system, active mirroredSystem - hier mirroredSystem.
    for top_mode, active_mode in [
        (M.INITIATOR, M.INITIATOR),
        (M.MIRRORED_TARGET, M.MIRRORED_TARGET),
        (M.TARGET, M.TARGET),
        (M.MIRRORED_INITIATOR, M.MIRRORED_INITIATOR),
        (M.SYSTEM, M.SYSTEM),
        (M.MIRRORED_SYSTEM, M.MIRRORED_SYSTEM),
    ]:
        assert _link_hier(top_mode, active_mode).diagnostics == [], (top_mode, active_mode)


def test_scr_2_4_reports_an_active_initiator_connected_to_a_hier_target():
    linked = _link_hier(M.TARGET, M.INITIATOR)

    [diagnostic] = _rule(linked, "SCR 2.4")
    assert diagnostic.message == (
        "interconnection 'conn0' connects s0/bif (active initiator) to hierInterface 'bif' "
        "(hierarchical target), but an active initiator interface may only connect to active "
        "mirroredInitiator or active target or hierarchical initiator interfaces"
    )
    assert len(_rule(linked, "SCR 2.6")) == 1  # a hier target may only connect to an active target


def test_scr_2_5_reports_an_active_mirrored_target_connected_to_a_hier_target():
    assert len(_rule(_link_hier(M.TARGET, M.MIRRORED_TARGET), "SCR 2.5")) == 1


def test_scr_2_7_reports_a_hier_mirrored_initiator_connected_to_an_active_target():
    assert len(_rule(_link_hier(M.MIRRORED_INITIATOR, M.TARGET), "SCR 2.7")) == 1


def test_scr_2_8_reports_an_active_system_connected_to_an_active_system_once():
    sub = _component("sub", _bus_interface("bif", M.SYSTEM))
    design = _design(
        [_instance("s0", sub), _instance("s1", sub)], [_interconnection("conn0", ("s0", "bif"), ("s1", "bif"))]
    )

    linked = link(design, _make_library(_bus_definition(BUS_A), sub))

    assert len(_rule(linked, "SCR 2.8")) == 1
    assert _rule(linked, "SCR 2.10") == []  # an interconnection with system interfaces needs no driver


def test_scr_2_9_reports_an_active_mirrored_system_connected_to_a_hier_system():
    assert len(_rule(_link_hier(M.SYSTEM, M.MIRRORED_SYSTEM), "SCR 2.9")) == 1


def test_scr_2_10_reports_an_interconnection_without_a_driver():
    sub = _component("sub", _bus_interface("bif", M.TARGET))
    design = _design(
        [_instance("s0", sub), _instance("s1", sub)], [_interconnection("conn0", ("s0", "bif"), ("s1", "bif"))]
    )

    linked = link(design, _make_library(_bus_definition(BUS_A), sub))

    assert [d.message for d in _rule(linked, "SCR 2.10")] == [
        "interconnection 'conn0' has 0 driving interfaces (none), but needs exactly one: an active "
        "initiator or mirroredTarget, or a hierarchical target or mirroredInitiator"
    ]


def test_scr_2_10_is_not_checked_when_an_interface_does_not_resolve():
    # the interface that does not resolve may be the driver.
    sub = _component("sub", _bus_interface("bif", M.TARGET))
    design = _design([_instance("s0", sub)], [_interconnection("conn0", ("s0", "bif"), ("s0", "typo"))])

    linked = link(design, _make_library(_bus_definition(BUS_A), sub))

    assert len(_rule(linked, "SCR 2.1")) == 1
    assert _rule(linked, "SCR 2.10") == []


def _link_broadcast(bus_type, broadcast):
    initiator = _component("init", _bus_interface("bif", M.INITIATOR, bus_type))
    target = _component("tgt", _bus_interface("bif", M.TARGET, bus_type))
    top = _component("top", _bus_interface("bif", M.INITIATOR, bus_type), design=TOP_DESIGN)
    design = _design(
        [_instance("i0", initiator), _instance("t0", target), _instance("t1", target)],
        [_interconnection("conn0", ("i0", "bif"), ("t0", "bif"), ("t1", "bif"))],
    )
    return link(design, _make_library(_bus_definition(bus_type, broadcast), initiator, target, top))


def test_scr_2_17_reports_more_than_two_interfaces_on_a_bus_without_broadcast():
    linked = _link_broadcast(BUS_A, None)

    assert [d.message for d in _rule(linked, "SCR 2.17")] == [
        "interconnection 'conn0' has 3 activeInterface and hierInterface elements, but bus "
        "definition example.org:bus:bus_a:1.0 does not set broadcast to true"
    ]


def test_scr_2_17_allows_more_than_two_interfaces_on_a_broadcast_bus():
    assert _link_broadcast(BUS_BROADCAST, True).diagnostics == []


def test_scr_2_17_is_not_reported_by_the_single_doc_checks():
    # the design alone does not say whether the bus definition allows broadcast.
    design = _link_broadcast(BUS_A, None).design

    assert not any(d.rule_id == "SCR 2.17" for d in SCR.run_single_doc_checks(design))


def test_scr_2_3_reports_a_hier_interface_in_two_interconnections():
    design = _design([], [_interconnection("conn0", ("a0", "bif"), "m"), _interconnection("conn1", ("b0", "bif"), "m")])

    diagnostics = [d for d in SCR.run_single_doc_checks(design) if d.rule_id == "SCR 2.3"]

    assert [d.message for d in diagnostics] == ["hierInterface 'm' appears in more than one interconnection: conn0, conn1"]


def test_a_hier_interface_connected_to_itself_is_reported_by_link():
    sub = _component("sub", _bus_interface("m", M.INITIATOR))
    top = _component("top", _bus_interface("m", M.INITIATOR), design=TOP_DESIGN)
    design = _design([_instance("s0", sub)], [_interconnection("conn0", ("s0", "m"), "m", "m")])

    linked = link(design, _make_library(_bus_definition(BUS_A), sub, top))

    assert "interconnection 'conn0' connects hierInterface 'm' to itself" in [d.message for d in linked.diagnostics]


def test_scr_13_5_reports_ad_hoc_port_references_that_do_not_exist():
    sub = _component("sub", ports=[_port("clk")])
    top = _component("top", ports=[_port("clk_in")], design=TOP_DESIGN)
    design = _design(
        [_instance("s0", sub)],
        ad_hoc_connections=[
            ipxact.AdHocConnection(
                name="clk_net",
                internal_port_references=[
                    ipxact.InternalPortReference(component_instance_ref="s0", port_ref="clk"),
                    ipxact.InternalPortReference(component_instance_ref="s0", port_ref="typo"),
                    ipxact.InternalPortReference(component_instance_ref="nobody", port_ref="clk"),
                ],
                external_port_references=[
                    ipxact.ExternalPortReference(port_ref="clk_in"),
                    ipxact.ExternalPortReference(port_ref="clk_typo"),
                ],
            )
        ],
    )

    linked = link(design, _make_library(sub, top))

    assert [d.message for d in _rule(linked, "SCR 13.5")] == [
        "adHocConnection 'clk_net' internalPortReference portRef 'typo' does not match a port on "
        "component instance 's0'",
        "adHocConnection 'clk_net' internalPortReference componentInstanceRef 'nobody' does not "
        "resolve to a component instance",
        "adHocConnection 'clk_net' externalPortReference portRef 'clk_typo' does not match a port "
        "on component example.org:ip:top:1.0, which contains the design",
    ]
    assert [r.port.name for r in linked.ad_hoc_connections["clk_net"]] == ["clk"]
    assert [r.port.name for r in linked.ad_hoc_external_ports["clk_net"]] == ["clk_in"]


def test_scr_1_5_reports_design_refs_that_are_not_designs():
    sub = _component("sub")
    top = _component("top", design=TOP_DESIGN)
    top.model.design_instantiations.append(
        ipxact.DesignInstantiation(name="missing", design_ref=_vlnv_ref(ipxact.VLNV("example.org", "soc", "gone", "1.0")))
    )
    configuration = ipxact.DesignConfiguration(
        vlnv=ipxact.VLNV("example.org", "soc", "top_cfg", "1.0"), design_ref=_vlnv_ref(sub.vlnv)
    )

    linked = link(_design([]), _make_library(sub, top), design_configuration=configuration)

    assert [d.message for d in _rule(linked, "SCR 1.5")] == [
        "designConfiguration example.org:soc:top_cfg:1.0 designRef does not resolve to a design: "
        "VLNV example.org:ip:sub:1.0 resolves to a Component, not a design",
        "component example.org:ip:top:1.0 designInstantiation 'missing' designRef does not resolve to "
        "a design: no document with VLNV example.org:soc:gone:1.0 was found in the library",
    ]
