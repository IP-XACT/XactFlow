"""IEEE 1685-2022 Annex B, Table B.13: Design configurations (5 rules, SCR 13.1-13.5).

None of these are implemented yet; every rule is registered via stub() so it is tracked and
discoverable through SCR.all_rules().
"""

from __future__ import annotations

from .registry import stub

stub(
    id="SCR 13.1",
    table="B.13",
    name="ViewConfigInstanceExists",
    single_doc_check=False,
    post_config=False,
    description="The value of an instanceName within a viewConfiguration shall match the value of the instanceName element of a componentInstance of the design document referenced by the containing design configuration, or the design document referenced by the designInstantiation.",
)

stub(
    id="SCR 13.2",
    table="B.13",
    name="ViewConfigViewExists",
    single_doc_check=False,
    post_config=False,
    description="The value of a viewName within a viewConfiguration shall match the value of the name element of a view within the component referenced by the component instance that is itself referenced by the instanceName subelement of the viewConfiguration element.",
)

stub(
    id="SCR 13.3",
    table="B.13",
    name="ViewConfigsUnique",
    single_doc_check=True,
    post_config=True,
    description="No two viewConfiguration elements within a design configuration shall reference the same view, i.e. no two viewConfiguration elements may have the same instanceName.",
)

stub(
    id="SCR 13.4",
    table="B.13",
    name="AbstractorInstancesUnique",
    single_doc_check=True,
    post_config=False,
    description="No two abstractor elements within a design configuration shall have the same instanceName element values. The abstractor names shall also not overlap with component instance names within the design.",
)

stub(
    id="SCR 13.5",
    table="B.13",
    name="adhocPortRefExists",
    single_doc_check=False,
    post_config=False,
    description="A component view shall configure a componentInstantiation, designInstantiation, and designConfigurationInstantiation such that all design adHocConnection internalPortReferences exist in the configured design and all design adHocConnection externalPortReferences exist in the configured component.",
)
