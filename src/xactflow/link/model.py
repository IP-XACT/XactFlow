from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

import ipxact

from ..diagnostics import Diagnostic
from ..library import Library


@dataclass
class LinkedInstance:
    """One ipxact:componentInstance resolved to its actual Component object."""

    instance_name: str
    component: ipxact.Component
    component_vlnv: ipxact.VLNV
    source: ipxact.ComponentInstance


@dataclass
class ResolvedInterfaceEndpoint:
    """One interface endpoint (of an interconnection or a monitorInterconnection), resolved to
    its instance and bus interface."""

    instance: LinkedInstance
    bus_interface: ipxact.BusInterface
    source: Union[ipxact.ActiveInterface, ipxact.MonitorInterfaceRef]


@dataclass
class ResolvedHierInterface:
    """One ipxact:hierInterface resolved to the bus interface of the component containing the
    design (LinkedDesign.component)."""

    bus_interface: ipxact.BusInterface
    source: ipxact.HierInterface


@dataclass
class LinkedInterconnection:
    """One ipxact:interconnection with its active interfaces (endpoints) and hierInterfaces
    resolved. Those that could not be resolved are absent; source keeps all of them.
    """

    name: str
    endpoints: List[ResolvedInterfaceEndpoint] = field(default_factory=list)
    hier_interfaces: List[ResolvedHierInterface] = field(default_factory=list)
    source: Optional[ipxact.Interconnection] = None


@dataclass
class LinkedMonitorInterconnection:
    """One ipxact:monitorInterconnection with its active and monitor endpoints resolved."""

    name: str
    monitored_active_interface: ResolvedInterfaceEndpoint
    monitor_interfaces: List[ResolvedInterfaceEndpoint] = field(default_factory=list)
    source: Optional[ipxact.MonitorInterconnection] = None


@dataclass
class ResolvedPortReference:
    """One ipxact:internalPortReference resolved to its instance and physical Port."""

    instance: LinkedInstance
    port: ipxact.Port
    source: ipxact.InternalPortReference


@dataclass
class ResolvedExternalPortReference:
    """One ipxact:externalPortReference resolved to a Port of the component containing the
    design (LinkedDesign.component)."""

    port: ipxact.Port
    source: ipxact.ExternalPortReference


@dataclass
class LinkedDesign:
    """The result of resolving one Design (and optional DesignConfiguration) against a Library.

    Each reference that resolved points at the object it names, instead of a VLNV or a name. A
    reference that did not resolve is left out; `diagnostics` says why, and `design` still holds
    every reference as written.

    component is the component containing the design: the hierInterface and
    externalPortReference elements refer to its bus interfaces and ports. It is None when
    link() could not tell which component that is.
    """

    vlnv: ipxact.VLNV
    design: ipxact.Design
    library: Library
    instances: Dict[str, LinkedInstance] = field(default_factory=dict)
    interconnections: List[LinkedInterconnection] = field(default_factory=list)
    monitor_interconnections: List[LinkedMonitorInterconnection] = field(default_factory=list)
    ad_hoc_connections: Dict[str, List[ResolvedPortReference]] = field(default_factory=dict)
    ad_hoc_external_ports: Dict[str, List[ResolvedExternalPortReference]] = field(default_factory=dict)
    component: Optional[ipxact.Component] = None
    design_configuration: Optional[ipxact.DesignConfiguration] = None
    diagnostics: List[Diagnostic] = field(default_factory=list)
