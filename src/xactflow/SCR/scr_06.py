"""IEEE 1685-2022 Annex B, Table B.6: Ports (59 rules, SCR 6.1-6.59).

None of these are implemented yet; every rule is registered via stub() so it is tracked and
discoverable through SCR.all_rules().
"""

from __future__ import annotations

from .registry import stub

stub(
    id="SCR 6.1",
    table="B.6",
    name="LogicalPortNameExists",
    single_doc_check=False,
    post_config=False,
    description=(
        "The value of the name subelement of any logicalPort element within an "
        "abstractionType element shall match the value of a logicalName element of the "
        "abstraction definition referenced by the abstractionType element."
    ),
)

stub(
    id="SCR 6.2",
    table="B.6",
    name="LogPortRequiresPortDir",
    single_doc_check=False,
    post_config=False,
    description=(
        "If the abstraction definition referenced by an abstractionType specifies an "
        "initiative value of requires for a logical transactional port for that interface "
        "mode, the port map shall map that logical port only to a component port with an "
        "initiative value of requires, both, or phantom, or to a component port with an "
        "allLogicalInitiativesAllowed attribute value of true. For system interfaces, the "
        "port initiative values are looked up from the matching onSystem element; for "
        "mirrored interfaces, the bus port initiative values are reversed before comparison."
    ),
)

stub(
    id="SCR 6.3",
    table="B.6",
    name="LogPortProvidesPortDir",
    single_doc_check=False,
    post_config=False,
    description=(
        "If the abstraction definition referenced by an abstractionType specifies an "
        "initiative value of provides for a logical transactional port for that interface "
        "mode, the port map shall map that logical port only to a component port with an "
        "initiative value of provides, both, or phantom, or to a component port with an "
        "allLogicalInitiativesAllowed attribute value of true. For system interfaces, the "
        "port initiative values are looked up from the matching onSystem element; for "
        "mirrored interfaces, the bus port initiative values are reversed before comparison."
    ),
)

stub(
    id="SCR 6.4",
    table="B.6",
    name="LogPortBothPortDir",
    single_doc_check=False,
    post_config=False,
    description=(
        "If the abstraction definition referenced by an abstractionType specifies an "
        "initiative value of both for a logical transactional port for that interface mode "
        "and the bus interface has a port map, the port map shall map that logical port only "
        "to a component port with an initiative value of both or phantom, or to a component "
        "port with an allLogicalInitiativesAllowed attribute value of true. For system "
        "interfaces, the port initiative values are looked up from the matching onSystem "
        "element; for mirrored interfaces, the bus port initiative values are reversed "
        "before comparison."
    ),
)

stub(
    id="SCR 6.5",
    table="B.6",
    name="LogPortInPortDir",
    single_doc_check=False,
    post_config=False,
    description=(
        "If the abstraction definition referenced by an abstractionType specifies a "
        "direction of in for a logical wire port for that interface mode, the port map shall "
        "map that logical port only to a component port with a direction of in, inout, or "
        "phantom, or to a component port with an allLogicalDirectionsAllowed attribute value "
        "of true. For system interfaces, the port directions are looked up from the matching "
        "onSystem element; for mirrored interfaces, the bus port directions are reversed "
        "before comparison."
    ),
)

stub(
    id="SCR 6.6",
    table="B.6",
    name="LogPortOutPortDir",
    single_doc_check=False,
    post_config=False,
    description=(
        "If the abstraction definition referenced by an abstractionType specifies a "
        "direction of out for a logical wire port for that interface mode, the port map "
        "shall map that logical port only to a component port with a direction of out, "
        "inout, or phantom, or to a component port with an allLogicalDirectionsAllowed "
        "attribute value of true. For system interfaces, the port directions are looked up "
        "from the matching onSystem element; for mirrored interfaces, the bus port "
        "directions are reversed before comparison."
    ),
)

stub(
    id="SCR 6.7",
    table="B.6",
    name="LogPortInoutPortDir",
    single_doc_check=False,
    post_config=False,
    description=(
        "If the abstraction definition referenced by an abstractionType specifies a "
        "direction of inout for a logical wire port for that interface mode, the port map "
        "shall map that logical port only to a component port with a direction of inout or "
        "phantom, or to a component port with an allLogicalDirectionsAllowed attribute value "
        "of true. For system interfaces, the port directions are looked up from the matching "
        "onSystem element; for mirrored interfaces, the bus port directions are reversed "
        "before comparison."
    ),
)

stub(
    id="SCR 6.8",
    table="B.6",
    name="LogPortPresence",
    single_doc_check=False,
    post_config=False,
    description=(
        "If the abstraction definition referenced by an abstractionType specifies a presence "
        "value of required for a port for that interface mode and the bus interface has a "
        "port map, the port shall be in that port map. For system interfaces, the port "
        "presence is looked up from the matching onSystem element; mirrored bus interfaces "
        "are looked up as if not mirrored. Port maps are optional even on buses with "
        "required ports; presence does not apply to interfaces of type monitor."
    ),
)

stub(
    id="SCR 6.9",
    table="B.6",
    name="OneWireDriver",
    single_doc_check=False,
    post_config=True,
    description="Only one component port in a port connection equivalence class may have the direction out, unless it is an analog port.",
)

stub(
    id="SCR 6.10",
    table="B.6",
    name="OneTransactionalDriver",
    single_doc_check=False,
    post_config=True,
    description="Only one component port in a port connection equivalence class may have the initiative requires.",
)

stub(
    id="SCR 6.11",
    table="B.6",
    name="ExtendedLogPortsExist",
    single_doc_check=False,
    post_config=True,
    description=(
        "If abstraction definition A extends abstraction definition B, then A shall have "
        "port elements for every port declared in B. If a port in B is not used in bus "
        "interfaces using abstraction definition A, then in A that port shall have a "
        "presence value of illegal for all bus interface modes."
    ),
)

stub(
    id="SCR 6.12",
    table="B.6",
    name="LogicalWireToPhysicalWireOrStructured",
    single_doc_check=False,
    post_config=False,
    description=(
        "If the abstraction definition referenced by a bus or abstraction interface "
        "specifies a port is a wire port, the port map shall map that logical port only to a "
        "wire component port or a structured component (sub)port. If the physical port "
        "references a structured (sub)port then the (sub)port packed attribute shall be true "
        "or the logical port shall not have a width."
    ),
)

stub(
    id="SCR 6.13",
    table="B.6",
    name="LogicalTransToPhysicalTrans",
    single_doc_check=False,
    post_config=False,
    description=(
        "If the abstraction definition referenced by a bus or abstraction interface "
        "specifies a port is a transactional port, the port map shall map that logical port "
        "only to a transactional component port."
    ),
)

stub(
    id="SCR 6.14",
    table="B.6",
    name="LogPortSystemRefExists",
    single_doc_check=False,
    post_config=False,
    description=(
        "The value of the group subelement of an onSystem element shall match the value of "
        "one of the system group names referenced in the bus definition referenced by the "
        "abstraction definition containing the onSystem element."
    ),
)

stub(
    id="SCR 6.15",
    table="B.6",
    name="SystemGroupDefined",
    single_doc_check=False,
    post_config=False,
    description=(
        "The value of the group subelement of a system element shall match the value of one "
        "of the system group names referenced in the bus definition referenced by the bus "
        "interface containing the onSystem element."
    ),
)

stub(
    id="SCR 6.16",
    table="B.6",
    name="CantMapIllegalPresencePort",
    single_doc_check=False,
    post_config=True,
    description=(
        "If the abstraction definition defines ports with a presence value of illegal for a "
        "given interface mode, then the indicated ports may not appear in the port map of a "
        "bus interface of that mode type. For system interfaces, the port presence is looked "
        "up from the matching onSystem element; mirrored bus and abstraction interfaces are "
        "looked up as if not mirrored. Port maps are optional even on buses with required "
        "ports."
    ),
)

stub(
    id="SCR 6.17",
    table="B.6",
    name="PhysicalPortRangeExists",
    single_doc_check=True,
    post_config=False,
    description="The range of a physicalPort shall be a subset of the range of the referenced port in the component's model element.",
)

stub(
    id="SCR 6.18",
    table="B.6",
    name="LogicalRangeMatchesPhysical",
    single_doc_check=True,
    post_config=False,
    description="Within any portMap, the sizes of the ranges of the physicalPort and the logicalPort shall be equal.",
)

stub(
    id="SCR 6.19",
    table="B.6",
    name="LogicalRangeWithinDefinition",
    single_doc_check=False,
    post_config=False,
    description=(
        "If the abstraction definition port referenced by a logicalPort has a width defined, "
        "all elements in the range of the logical port shall be between width-1 and 0."
    ),
)

stub(
    id="SCR 6.20",
    table="B.6",
    name="LogicalBitsMappedOnlyOnce",
    single_doc_check=True,
    post_config=True,
    description=(
        "Within a single bus interface, no logical bit may be mapped more than once, i.e. if "
        "two or more logicalPort elements for that bus interface reference the same "
        "abstraction definition port, their ranges shall not overlap."
    ),
)

stub(
    id="SCR 6.21",
    table="B.6",
    name="TransactionalPortBusConnection",
    single_doc_check=False,
    post_config=False,
    description=(
        "If a transactional port in a component is mapped in a bus interface to a "
        "transactional port in an abstraction definition, then the initiative, kind, "
        "busWidth, and protocolType elements in that component port shall match those "
        "defined in the abstraction definition's port."
    ),
)

stub(
    id="SCR 6.22",
    table="B.6",
    name="TransactionalPortConnection",
    single_doc_check=False,
    post_config=False,
    description=(
        "Transactional ports shall be connected together (by an ad hoc connection or through "
        "an interconnection) only if they have compatible initiative, busWidth, kind, and "
        "protocol elements and if none of them contains a transTypeDefs element or all of "
        "them contain compatible transTypeDefs elements. Two initiatives with any "
        "provides-requires combination are compatible; two kinds are compatible if equal or "
        "both sockets; two busWidths are compatible if equal; two protocols are compatible "
        "if both tlm, or both custom with matching payloads if defined; two transTypeDefs "
        "are compatible if their typeParameters are equal and serviceTypeDefs typeNames "
        "match when defined and not implicit."
    ),
)

stub(
    id="SCR 6.23",
    table="B.6",
    name="CantDriveOutputPort",
    single_doc_check=True,
    post_config=True,
    description="A wire port with a direction of out shall not have a driver element.",
)

stub(
    id="SCR 6.24",
    table="B.6",
    name="AdHocPortWidthsMatch",
    single_doc_check=False,
    post_config=False,
    description=(
        "All wire (sub)ports and all structured (sub)ports with attribute packed set to true "
        "referenced in an ad hoc connection shall reference the same number of bits. If no "
        "range is specified for a non-scalar port, the full range from the port definition "
        "is presumed."
    ),
)

stub(
    id="SCR 6.25",
    table="B.6",
    name="TiedValueDefaultHasDefault",
    single_doc_check=False,
    post_config=False,
    description="All ports referenced in an ad hoc connection that has a tiedValue of default shall have a default value defined.",
)

stub(
    id="SCR 6.26",
    table="B.6",
    name="ViewlessComponentRestriction",
    single_doc_check=True,
    post_config=True,
    description="A component without views shall contain only phantom ports.",
)

stub(
    id="SCR 6.27",
    table="B.6",
    name="VirtualComponentRestriction",
    single_doc_check=True,
    post_config=True,
    description="If isVirtual is true in a componentInstantiation element, then views referencing that componentInstantiation shall contain only phantom ports.",
)

stub(
    id="SCR 6.28",
    table="B.6",
    name="StructuredDirectionMatch",
    single_doc_check=True,
    post_config=False,
    description="All values of all direction elements contained within wire, structured, and union elements within a structured element shall be equal.",
)

stub(
    id="SCR 6.29",
    table="B.6",
    name="isIOPresence",
    single_doc_check=True,
    post_config=False,
    description="The isIO element shall only be present on a subPort contained within a structured element that has an interface element.",
)

stub(
    id="SCR 6.30",
    table="B.6",
    name="PowerConstraintRangeRequirement",
    single_doc_check=True,
    post_config=False,
    description="The bits referenced by a powerConstraint range element must exist within the containing wire port.",
)

stub(
    id="SCR 6.31",
    table="B.6",
    name="PowerConstraintOverlap",
    single_doc_check=True,
    post_config=True,
    description="The bits referenced by different powerConstraint range elements within the same port shall not overlap.",
)

stub(
    id="SCR 6.32",
    table="B.6",
    name="AnalogDefaultValueCount",
    single_doc_check=True,
    post_config=True,
    description=(
        "The defaultValue within a driver element of an analog port defined as a vector "
        "shall be defined as a realVectorExpression and the number of elements of the "
        "default value should match the width of the port."
    ),
)

stub(
    id="SCR 6.33",
    table="B.6",
    name="matchPorts",
    single_doc_check=False,
    post_config=True,
    description=(
        "If the abstraction definition referenced by a bus or abstraction interface "
        "specifies, for a port mapped in the bus-interface, a match value of true, the bus "
        "interface can only be connected to a bus interface which maps this same port."
    ),
)

stub(
    id="SCR 6.34",
    table="B.6",
    name="allBits",
    single_doc_check=False,
    post_config=True,
    description=(
        "If an abstraction definition port has a width defined with allBits set, any bus "
        "interface containing a port map referencing that port shall map all the bits of "
        "that port, i.e. every bit in the range [width-1:0] shall be mapped precisely once "
        "in the port maps of that bus interface."
    ),
)

stub(
    id="SCR 6.35",
    table="B.6",
    name="busDefinitionExtendsDirectConnection",
    single_doc_check=False,
    post_config=False,
    description="If bus definition A extends bus definition B, then A cannot specify a different value for directConnection.",
)

stub(
    id="SCR 6.36",
    table="B.6",
    name="busDefinitionExtendsBroadcast",
    single_doc_check=False,
    post_config=False,
    description="If bus definition A extends bus definition B, then A cannot specify a different value for broadcast.",
)

stub(
    id="SCR 6.37",
    table="B.6",
    name="busDefinitionExtendsIsAddressable",
    single_doc_check=False,
    post_config=False,
    description="If bus definition A extends bus definition B, then A cannot specify a different value for isAddressable.",
)

stub(
    id="SCR 6.38",
    table="B.6",
    name="busDefinitionExtendsMaxInitiators",
    single_doc_check=False,
    post_config=True,
    description="If bus definition A extends bus definition B, then A cannot specify a higher number for maxInitiators.",
)

stub(
    id="SCR 6.39",
    table="B.6",
    name="busDefinitionExtendsMaxTargets",
    single_doc_check=False,
    post_config=True,
    description="If bus definition A extends bus definition B, then A cannot specify a higher number for maxTargets.",
)

stub(
    id="SCR 6.40",
    table="B.6",
    name="busDefinitionExtendsSystemGroupNames",
    single_doc_check=False,
    post_config=False,
    description="If bus definition A extends bus definition B, then A can only add new group names.",
)

stub(
    id="SCR 6.41",
    table="B.6",
    name="abstractionDefinitionPortExtendsQualifiers",
    single_doc_check=False,
    post_config=False,
    description="If a port in abstraction definition A extends a port in abstraction definition B, then the extending port in A cannot specify different qualifiers.",
)

stub(
    id="SCR 6.42",
    table="B.6",
    name="abstractionDefinitionPortExtendsDirection",
    single_doc_check=False,
    post_config=False,
    description="If a port in abstraction definition A extends a port in abstraction definition B, then the extending port in A cannot specify a different direction.",
)

stub(
    id="SCR 6.43",
    table="B.6",
    name="abstractionDefinitionPortExtendsInitiative",
    single_doc_check=False,
    post_config=False,
    description="If a port in abstraction definition A extends a port in abstraction definition B, then the extending port in A cannot specify a different initiative.",
)

stub(
    id="SCR 6.44",
    table="B.6",
    name="abstractionDefinitionPortExtendsKind",
    single_doc_check=False,
    post_config=False,
    description="If a port in abstraction definition A extends a port in abstraction definition B, then the extending port in A cannot specify a different kind.",
)

stub(
    id="SCR 6.45",
    table="B.6",
    name="abstractionDefinitionPortExtendsBusWidth",
    single_doc_check=False,
    post_config=True,
    description="If a port in abstraction definition A extends a port in abstraction definition B, then the extending port in A cannot specify a different busWidth.",
)

stub(
    id="SCR 6.46",
    table="B.6",
    name="abstractionDefinitionPortExtendsProtocol",
    single_doc_check=False,
    post_config=False,
    description="If a port in abstraction definition A extends a port in abstraction definition B, then the extending port in A cannot specify a different protocol.",
)

stub(
    id="SCR 6.47",
    table="B.6",
    name="abstractionDefinitionPacketFieldEarlierWidth",
    single_doc_check=True,
    post_config=False,
    description="If a packetField width expression uses $ipxact_packetfield_value(), then the referenced packetField must be earlier in the packet.",
)

stub(
    id="SCR 6.48",
    table="B.6",
    name="abstractionDefinitionPacketFieldValueFits",
    single_doc_check=True,
    post_config=False,
    description="If a packetField value is specified, then the expression must have the same number of bits as the width of that packetField.",
)

stub(
    id="SCR 6.49",
    table="B.6",
    name="abstractionDefinitionPacketFieldFixedOpcode",
    single_doc_check=True,
    post_config=False,
    description="If a packetField has the isOpcode qualifier, then it must have a fixed value.",
)

stub(
    id="SCR 6.50",
    table="B.6",
    name="WireAndStructuredPortConnection",
    single_doc_check=False,
    post_config=False,
    description=(
        "Wire and structured ports shall be connected together (by an ad hoc connection or "
        "through an interconnection) only if they are compatible: two wire (sub)ports are "
        "compatible; a wire (sub)port and a structured (sub)port are compatible if the "
        "structured port is packed; two structured (sub)ports are compatible if both are "
        "packed, or if both are unpacked and have the same type (both struct, both union, or "
        "both interface, with matching typeName, typeDefinition, and typeParameters)."
    ),
)

stub(
    id="SCR 6.51",
    table="B.6",
    name="constrainedRefArrayAndVectorId",
    single_doc_check=True,
    post_config=True,
    description="A constrained attribute in a typeName element shall reference arrayId and vectorId attribute values of elements that are contained in the encapsulating port.",
)

stub(
    id="SCR 6.52",
    table="B.6",
    name="structuredViewRefsAreConsistent",
    single_doc_check=True,
    post_config=False,
    description="viewRef elements in subPort wireTypeDef and structPortTypeDef elements shall reference the same views as the encapsulating structured port structPortTypeDef viewRef elements.",
)

stub(
    id="SCR 6.53",
    table="B.6",
    name="isIoPortEquivalenceClass",
    single_doc_check=False,
    post_config=True,
    description="In a structured interface port connection equivalence class, all subPorts with attribute isIO set to true that are named the same shall have the same port equivalence class.",
)

stub(
    id="SCR 6.54",
    table="B.6",
    name="structPortParamValuesAreEqual",
    single_doc_check=False,
    post_config=True,
    description="All the configured structured interface port parameters defined on the component instances that contribute to a structured interface port connection equivalence class shall resolve to the same value.",
)

stub(
    id="SCR 6.55",
    table="B.6",
    name="partSelectIndices",
    single_doc_check=False,
    post_config=True,
    description="The indices of a partSelect element applied to a port reference shall select elements in the dimensions of that referenced port.",
)

stub(
    id="SCR 6.56",
    table="B.6",
    name="partSelectRangeOnLeaves",
    single_doc_check=False,
    post_config=True,
    description="In a reference to a structured port, explicit partSelect or implicit range element shall be applied only to the leave ports in the port reference.",
)

stub(
    id="SCR 6.57",
    table="B.6",
    name="noInterfaceInStructOrUnion",
    single_doc_check=True,
    post_config=False,
    description="A structured port or subPort containing a struct or union element shall not have subPort elements that contain an interface element.",
)

stub(
    id="SCR 6.58",
    table="B.6",
    name="structPortVectorRequiresPacked",
    single_doc_check=True,
    post_config=False,
    description="A structured port cannot contain a vector if the packed attribute is set to false.",
)

stub(
    id="SCR 6.59",
    table="B.6",
    name="structPortInterfaceRequiresUnpacked",
    single_doc_check=True,
    post_config=False,
    description="A structured port cannot contain an interface element if the packed attribute is set to true.",
)
