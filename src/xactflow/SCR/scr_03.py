"""IEEE 1685-2022 Annex B, Table B.3: Channels, bridges, and abstractors (18 rules, SCR 3.1-3.18).

None of these are implemented yet; every rule is registered via stub() so it is tracked and
discoverable through SCR.all_rules().
"""

from __future__ import annotations

from .registry import stub

stub(
    id="SCR 3.1",
    table="B.3",
    name="ChannelAbsDefsCompat",
    single_doc_check=False,
    post_config=True,
    description=(
        "Within a channel element, all the busInterfaceRef elements shall refer to compatible "
        "abstraction definitions, i.e. the VLNVs of the abstractionType elements within the "
        "busInterface elements shall reference compatible abstractionDefinitions. "
        "Compatibility of the abstraction definitions implies compatibility of their "
        "associated bus definitions."
    ),
)

stub(
    id="SCR 3.2",
    table="B.3",
    name="ChannelIntfsMirrored",
    single_doc_check=True,
    post_config=False,
    description="All bus interfaces referenced by a channel shall be mirrored interfaces.",
)

stub(
    id="SCR 3.3",
    table="B.3",
    name="MaxInitiatorsHonored",
    single_doc_check=False,
    post_config=True,
    description=(
        "A channel can be connected to no more mirrored-initiator busInterfaces than the "
        "least value of maxInitiators in the bus definitions referenced by the connected bus "
        "interfaces. A channel may connect ports with different bus definitions, and hence "
        "different values of maxInitiators, as long as the bus definitions are compatible."
    ),
)

stub(
    id="SCR 3.4",
    table="B.3",
    name="MaxTargetsHonored",
    single_doc_check=False,
    post_config=True,
    description=(
        "A channel can be connected to no more mirrored-target bus interfaces than the least "
        "value of maxTargets in the bus definitions referenced by the connected bus "
        "interfaces. A channel may connect ports with different bus definitions, and hence "
        "different values of maxTargets, as long as the bus definitions are compatible."
    ),
)

stub(
    id="SCR 3.5",
    table="B.3",
    name="BusIntfInOneChannelMax",
    single_doc_check=True,
    post_config=True,
    description="Each bus interface on a component shall connect to only one channel of that channel component.",
)

stub(
    id="SCR 3.6",
    table="B.3",
    name="InitiatorRefIntfIsInitiator",
    single_doc_check=True,
    post_config=False,
    description="The interface referenced by initiatorRef subelement of a bridge element shall be an initiator.",
)

stub(
    id="SCR 3.7",
    table="B.3",
    name="InterConnectionRefMustMatch",
    single_doc_check=False,
    post_config=False,
    description=(
        "The value of the interconnectionRef subelement of an interconnectionConfiguration "
        "element shall precisely match a design interconnection/name or a design "
        "monitorInterconnection/name of an interconnection described in the design referenced "
        "by the containing design configuration or referenced by the design in the "
        "designInstantiation referenced by the view referencing the containing design "
        "configuration."
    ),
)

stub(
    id="SCR 3.8",
    table="B.3",
    name="AbstractorModeMustBeInitiator",
    single_doc_check=False,
    post_config=False,
    description=(
        "An abstractors element of an interconnectionConfiguration element in a design "
        "configuration document that references an initiator-to-mirrored-initiator "
        "connection shall reference only abstractors with an abstractorMode of initiator."
    ),
)

stub(
    id="SCR 3.9",
    table="B.3",
    name="AbstractorModeMustBeTarget",
    single_doc_check=False,
    post_config=False,
    description=(
        "An abstractors element of an interconnectionConfiguration element in a design "
        "configuration document that references a target-to-mirrored-target interconnection "
        "in the corresponding design shall reference only abstractors with an abstractorMode "
        "of target."
    ),
)

stub(
    id="SCR 3.10",
    table="B.3",
    name="AbstractorModeMustBeSystem",
    single_doc_check=False,
    post_config=False,
    description=(
        "An abstractors element of an interconnectionConfiguration element in a design "
        "configuration document that references a system-to-mirrored-system interconnection "
        "in the corresponding design shall reference only abstractors with an abstractorMode "
        "of system."
    ),
)

stub(
    id="SCR 3.11",
    table="B.3",
    name="AbstractModeMustBeDirect",
    single_doc_check=False,
    post_config=False,
    description=(
        "An abstractors element of an interconnectionConfiguration element in a design "
        "configuration document that references an initiator-to-target interconnection in "
        "the corresponding design shall reference only abstractors with an abstractorMode of "
        "direct."
    ),
)

stub(
    id="SCR 3.12",
    table="B.3",
    name="AbstractionChainStart",
    single_doc_check=False,
    post_config=False,
    description=(
        "In the list of abstractor elements within an abstractors element in an "
        "interconnectionConfiguration element, the first abstractionType element of the first "
        "referenced abstractor shall be compatible with the abstractionType element of the "
        "initiator, system, or mirrored-target endpoint of the interconnection."
    ),
)

stub(
    id="SCR 3.13",
    table="B.3",
    name="AbstractionChainEnd",
    single_doc_check=False,
    post_config=False,
    description=(
        "In the list of abstractor elements within an abstractors element an "
        "interconnectionConfiguration element, the second abstractionType element of the "
        "last referenced abstractor shall be compatible with the abstractionType element of "
        "the mirrored-initiator, mirrored-system, or target endpoint of the interconnection."
    ),
)

stub(
    id="SCR 3.14",
    table="B.3",
    name="AbstractionChainMiddle",
    single_doc_check=False,
    post_config=False,
    description=(
        "In the list of abstractor elements within an abstractors element an "
        "interconnectionConfiguration element, the first abstractionType element of every "
        "referenced abstractor, except the first, shall be compatible with the second "
        "abstractionType element of the previous abstractor in the interconnectionConfiguration "
        "list. SCR 3.12-SCR 3.14 together mean the abstractors associated with an "
        "interconnection need to form a non-looping chain between the two ends."
    ),
)

stub(
    id="SCR 3.15",
    table="B.3",
    name="AbstractionBusTypesMustMatch",
    single_doc_check=False,
    post_config=False,
    description=(
        "The VLNVs in the busType elements of both abstraction definitions referenced by an "
        "abstractor shall exactly match the VLNV in the busType element of the abstractor."
    ),
)

stub(
    id="SCR 3.16",
    table="B.3",
    name="AbstractionExtendsCondition",
    single_doc_check=False,
    post_config=False,
    description=(
        "If abstraction definition AA is an abstraction of bus definition A and abstraction "
        "definition AB is an abstraction of bus definition B, then AA shall contain an "
        "extends element referencing AB only if bus definition A contains an extends element "
        "referencing bus definition B. If AA extends AB, AA and AB need to be abstractions of "
        "different buses."
    ),
)

stub(
    id="SCR 3.17",
    table="B.3",
    name="SubspaceInitiatorRefExists",
    single_doc_check=True,
    post_config=False,
    description="The interface referenced by the initiatorRef attribute of a subspaceMap element shall be an initiator interface.",
)

stub(
    id="SCR 3.18",
    table="B.3",
    name="multiAbstractorBroadcast",
    single_doc_check=True,
    post_config=False,
    description=(
        "If multiple abstractors elements appear in an interconnectionConfiguration, then the "
        "referenced interconnection shall be a broadcast connection, i.e. contain more than "
        "two interfaces."
    ),
)
