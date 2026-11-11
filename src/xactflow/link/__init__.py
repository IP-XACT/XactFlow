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
from .resolver import link

__all__ = [
    "LinkedDesign",
    "LinkedInstance",
    "LinkedInterconnection",
    "LinkedMonitorInterconnection",
    "ResolvedExternalPortReference",
    "ResolvedHierInterface",
    "ResolvedInterfaceEndpoint",
    "ResolvedPortReference",
    "link",
]
