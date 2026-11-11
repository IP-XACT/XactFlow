"""IEEE 1685-2022 Annex B, Table B.13: Design configurations (5 rules, SCR 13.1-13.5).

SCR 13.5 is implemented, exercised by link.resolver. Every other rule in this table is
registered via stub() so it is tracked and discoverable through SCR.all_rules(), with no check
logic yet.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from ..diagnostics import Diagnostic, Severity
from .registry import rule, stub

if TYPE_CHECKING:
    from ..link.model import LinkedDesign

stub(
    id="SCR 13.1",
    table="B.13",
    name="ViewConfigInstanceExists",
    single_doc_check=False,
    post_config=False,
    description="The value of an instanceName within a viewConfiguration shall match the value of the instanceName element of a componentInstance of the design document referenced by the design configuration document containing the viewConfiguration element, or design document referenced by the designInstantiation.",
)

stub(
    id="SCR 13.2",
    table="B.13",
    name="ViewConfigViewExists",
    single_doc_check=False,
    post_config=False,
    description="The value of an viewName within a viewConfiguration shall match the value of the name element of a view within the component referenced by the component instance that is itself referenced by the instanceName subelement of the viewConfiguration element.",
)

stub(
    id="SCR 13.3",
    table="B.13",
    name="ViewConfigsUnique",
    single_doc_check=True,
    post_config=True,
    description="No two viewConfiguration elements within a design configuration shall reference the same view. i.e., no two viewConfiguration elements may have the same instanceName.",
)

stub(
    id="SCR 13.4",
    table="B.13",
    name="AbstractorInstancesUnique",
    single_doc_check=True,
    post_config=False,
    description="No two abstractor elements within a design configuration shall have the same instanceName element values. The abstractor names shall also not overlap with component instance names within the design.",
)

@rule(
    id="SCR 13.5",
    table="B.13",
    name="adhocPortRefExists",
    single_doc_check=False,
    post_config=False,
    description="A component view shall configure a componentInstantiation, designInstantiation, and designConfigurationInstantiation such that all design adHocConnection internalPortReferences exist in the configured design and all design adHocConnection externalPortReferences exist in the configured component.",
)
def _check_ad_hoc_port_refs_exist(linked: "LinkedDesign") -> Iterator[Diagnostic]:
    design_instance_names = {instance.instance_name for instance in linked.design.component_instances}
    component = linked.component
    component_ports = set()
    if component is not None and component.model is not None:
        component_ports = {port.name for port in component.model.ports}
    for ad_hoc in linked.design.ad_hoc_connections:
        location = f"{linked.vlnv}/{ad_hoc.name}"
        for reference in ad_hoc.internal_port_references:
            instance = linked.instances.get(reference.component_instance_ref)
            if instance is None:
                if reference.component_instance_ref in design_instance_names:
                    continue  # the instance's component is missing: SCR 1.9 reports it
                problem = (
                    f"componentInstanceRef '{reference.component_instance_ref}' does not resolve "
                    f"to a component instance"
                )
            elif instance.component.model is None or not any(
                port.name == reference.port_ref for port in instance.component.model.ports
            ):
                problem = (
                    f"portRef '{reference.port_ref}' does not match a port on component instance "
                    f"'{instance.instance_name}'"
                )
            else:
                continue
            yield Diagnostic(
                message=f"adHocConnection '{ad_hoc.name}' internalPortReference {problem}",
                severity=Severity.ERROR,
                location=location,
                rule_id="SCR 13.5",
                rule_name="adhocPortRefExists",
            )
        if component is None:
            continue  # link() warned, if there is any externalPortReference
        for reference in ad_hoc.external_port_references:
            if reference.port_ref in component_ports:
                continue
            yield Diagnostic(
                message=(
                    f"adHocConnection '{ad_hoc.name}' externalPortReference portRef "
                    f"'{reference.port_ref}' does not match a port on component {component.vlnv}, "
                    f"which contains the design"
                ),
                severity=Severity.ERROR,
                location=location,
                rule_id="SCR 13.5",
                rule_name="adhocPortRefExists",
            )
