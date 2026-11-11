"""IEEE 1685-2022 Annex B, Table B.7: Registers (31 rules, SCR 7.1-7.31).

None of these are implemented yet; every rule is registered via stub() so it is tracked and
discoverable through SCR.all_rules(). Most of the overlap/alignment rules here need real
IP-XACT expression evaluation (addressOffset, size, range, etc. are unevaluated strings in
ipxact-compiler's object model), which XactFlow does not implement yet either.
"""

from __future__ import annotations

from .registry import stub

stub(
    id="SCR 7.1",
    table="B.7",
    name="RegisterOverlap",
    single_doc_check=False,
    post_config=True,
    description=(
        "No register shall have an addressOffset that falls within the address range of "
        "another register in the same address block, unless one of the registers and their "
        "alternateRegisters have non-conflicting computed register access value; see C.2 and "
        "C.3. The address range of a register is the range [addressOffset, addressOffset + "
        "registerSize - 1] where registerSize is the size of the register in addressUnitBits. "
        "This is equal to dim[n-1]*dim[n]*...*dim[0]*stride, where dim is the maximum number "
        "of elements for each of n dimensions. In other words, multiple readable and multiple "
        "writeable registers shall not overlap. Note that in this SCR, the least restrictive "
        "access values in the relevant accessPolicies and fieldAccessPolicies shall be used to "
        "determine the computed access values independent of the value of the mode conditions; "
        "see C.3."
    ),
)

stub(
    id="SCR 7.2",
    table="B.7",
    name="BitOverlap",
    single_doc_check=False,
    post_config=True,
    description=(
        "No bit field shall have a bitOffset value that falls within the bit range of another "
        "bit field, unless one of the bit fields has computed access value read-only and the "
        "other has computed access value write-only, writeOnce, or no-access; see C.2 and C.3. "
        "The bit range of a bit field is the range [bitOffset, bitOffset + bitFieldWidth - 1] "
        "where bitFieldWidth is the size of a field in bits. This is equal to "
        "dim[n-1]*dim[n]*...*dim[0]*bitStride, where dim is the maximum number of elements for "
        "each of n dimensions. In other words, multiple readable bit fields and multiple "
        "writeable bit fields shall not overlap. Note that in this SCR, the least restrictive "
        "access values in the relevant accessPolicies and fieldAccessPolicies shall be used to "
        "determine the computed access values independent of the value of the mode conditions; "
        "see C.3."
    ),
)

stub(
    id="SCR 7.3",
    table="B.7",
    name="RegisterWithinBlock",
    single_doc_check=False,
    post_config=True,
    description="Any register in an address block shall fall entirely within that address block, i.e., for every register 0 <= addressOffset <= addressBlockRange - registerSize, where addressBlockRange is the range of the address block and registerSize is the size of the register in addressUnitBits. This is equal to dim[n-1]*dim[n]*...*dim[0]*stride, where dim is the maximum number of elements for each of n dimensions.",
)

stub(
    id="SCR 7.4",
    table="B.7",
    name="BitWithinRegister",
    single_doc_check=False,
    post_config=True,
    description="Any bit field in a register shall fall entirely within that register, i.e., for every bit field 0 <= bitOffset <= registerSize – bitFieldWidth, where registerSize is the size of the register in bits and bitFieldWidth is the width of a bit field. This is equal to dim[n-1]*dim[n]*...*dim[0]*bitStride, where dim is the maximum number of elements for each of n dimensions.",
)

stub(
    id="SCR 7.5",
    table="B.7",
    name="RegisterSizeWithinBlock",
    single_doc_check=False,
    post_config=True,
    description="The size of any register shall be no greater than the width of the containing address block.",
)

stub(
    id="SCR 7.6",
    table="B.7",
    name="RegisterWithinRegisterFile",
    single_doc_check=False,
    post_config=True,
    description="Any register in a register file shall fall entirely within that register file, i.e., for every register 0 <= register.addressOffset <= registerFileRange - registerSize, where registerFileRange is the range of the register file and registerSize is the size of the register in addressUnitBits. This is equal to dim[n-1]*dim[n]*...*dim[0]*stride, where dim is the maximum number of elements for each of n dimensions.",
)

stub(
    id="SCR 7.7",
    table="B.7",
    name="RegisterFileWithinBlock",
    single_doc_check=False,
    post_config=True,
    description="Any register file in an address block shall fall entirely within that address block, i.e., for every register file 0 <= registerFile.addressOffset <= addressBlockRange - registerFileSize, where addressBlockRange is the range of the address block and registerFileSize is the size of the register file in addressUnitBits. This is equal to dim[n-1]*dim[n]*...*dim[0]*stride, where dim is the maximum number of elements for each of n dimensions.",
)

stub(
    id="SCR 7.8",
    table="B.7",
    name="BlockVolatileCondition",
    single_doc_check=False,
    post_config=True,
    description="volatile cannot be set to false for an addressBlock where any containing register or field already has volatile set to true.",
)

stub(
    id="SCR 7.9",
    table="B.7",
    name="RegisterVolatileCondition",
    single_doc_check=False,
    post_config=True,
    description="volatile cannot be set to false for a register where any containing field already has volatile set to true.",
)

stub(
    id="SCR 7.10",
    table="B.7",
    name="FieldUseEnumCondition",
    single_doc_check=True,
    post_config=True,
    description="When a field has writeValueConstraint/ useEnumeratedValues set to true, it also shall have at least one enumeratedValue with the attribute usage set to write or read-write.",
)

stub(
    id="SCR 7.11",
    table="B.7",
    name="FieldConstraintRangeCondition",
    single_doc_check=True,
    post_config=True,
    description="When a field has a writeValueConstraint/ minimum value and has a writeValueConstraint/maximum value, the value of maximum shall be greater than or equal to the value of minimum.",
)

stub(
    id="SCR 7.12",
    table="B.7",
    name="FieldTypeIdentifierCondition",
    single_doc_check=True,
    post_config=True,
    description=(
        "When multiple field elements have the same typeIdentifier, the field object shall "
        "contain the same contents for the elements in the fieldDefinitionGroup. For a field "
        "with an aliasOf element, the bitWidth, volatile, and resets of the field object is "
        "the bitWidth, volatile, and resets of the aliased field."
    ),
)

stub(
    id="SCR 7.13",
    table="B.7",
    name="RegisterTypeIdentiferCondition",
    single_doc_check=True,
    post_config=True,
    description=(
        "When multiple register or alternateRegister elements have the same typeIdentifier, "
        "the register object shall contain the same contents for the elements in the "
        "registerDefinitionGroup or alternateRegisterDefinitionGroup. For an "
        "alternateRegister element, the size of the register object is the size of the "
        "encapsulating register element."
    ),
)

stub(
    id="SCR 7.14",
    table="B.7",
    name="RegisterFileTypeIdentifierCondition",
    single_doc_check=True,
    post_config=True,
    description="When multiple registerFile elements have the same typeIdentifier, the register file object shall contain the same contents for the elements in the registerFileDefinitionGroup.",
)

stub(
    id="SCR 7.15",
    table="B.7",
    name="BlockTypeIdentifierCondition",
    single_doc_check=True,
    post_config=True,
    description="When multiple addressBlock elements have the same typeIdentifier, the address block object shall contain the same contents for the elements in the addressBlockDefinitionGroup.",
)

stub(
    id="SCR 7.16",
    table="B.7",
    name="noWritePropsInROField",
    single_doc_check=True,
    post_config=True,
    description="A register field whose access type does not allow writing (access type read-only or no-access) shall not include any of the following subelements: modifiedWriteValue.",
)

stub(
    id="SCR 7.17",
    table="B.7",
    name="noReadPropsInWOField",
    single_doc_check=True,
    post_config=True,
    description="A register field whose access type does not allow reading (access types of write-only, writeOnce or no-access) shall not include any of the following subelements: readAction.",
)

stub(
    id="SCR 7.18",
    table="B.7",
    name="registerFileOverlap",
    single_doc_check=False,
    post_config=True,
    description="No register or register file shall have an addressOffset that falls within the address range of another register file in the same address block. The address range of a register file is the range [addressOffset, addressOffset + registerFileSize - 1] where registerFileSize is the size of the register file in addressUnitBits. This is equal to dim[n-1]*dim[n]*...*dim[0]*stride, where dim is the maximum number of elements for each of n dimensions.",
)

stub(
    id="SCR 7.19",
    table="B.7",
    name="resetTypeHARD",
    single_doc_check=True,
    post_config=False,
    description="A resetType with a name of HARD shall not be specified.",
)

stub(
    id="SCR 7.20",
    table="B.7",
    name="resetTypeRefUnspecified",
    single_doc_check=True,
    post_config=False,
    description="Only one resetValue can be specified without a resetTypeRef (indicating the default/HARD reset-type) on a field.",
)

stub(
    id="SCR 7.21",
    table="B.7",
    name="aliasOfReference",
    single_doc_check=False,
    post_config=False,
    description=(
        "An aliasOf element shall reference another field in the same component, "
        "registerDefinition, registerFileDefinition, addressBlockDefinition, bankDefinition, "
        "memoryMapDefinition, or memoryReMapDefinition that does not have an aliasOf element. "
        "Note that a component and typeDefinition may be defined using multiple files due to "
        "referencing of external typeDefinitions files."
    ),
)

stub(
    id="SCR 7.22",
    table="B.7",
    name="broadcastToReference",
    single_doc_check=False,
    post_config=False,
    description="A broadcastTo element shall reference another field in the same component, registerDefinition, registerFileDefinition, addressBlockDefinition, bankDefinition, memoryMapDefinition, or memoryReMapDefinition . Note that a component and typeDefinitions may be defined using multiple files due to referencing of external typeDefinitions files.",
)

stub(
    id="SCR 7.23",
    table="B.7",
    name="uniqueBitFieldDriver",
    single_doc_check=False,
    post_config=False,
    description=(
        "A field access shall drive a bit field only once, i.e., a field or fieldDefinition "
        "field connection graph shall not contain an instance node that can be reached from "
        "more than one mapping node starting at a single mapping node. Note that in this SCR, "
        "the least restrictive access values in the relevant accessPolicies and "
        "fieldAccessPolicies shall be used to determine the computed access values independent "
        "of the value of the mode conditions; see C.3."
    ),
)

stub(
    id="SCR 7.24",
    table="B.7",
    name="noFieldWriteCycle",
    single_doc_check=False,
    post_config=False,
    description="Field write accesses shall be single transactions, i.e., a field or fieldDefinition field connection graph shall not contain cycles containing more than one mapping node. Note that in this SCR, the least restrictive access values in the relevant accessPolicies and fieldAccessPolicies shall be used to determine the computed access values independent of the value of the mode conditions; see C.3.",
)

stub(
    id="SCR 7.25",
    table="B.7",
    name="EnumeratedValueWidth",
    single_doc_check=False,
    post_config=False,
    description="The width of value elements within an enumeratedValues list for a register field (whether specified explicitly or within an enumerationDefinition) must be less than or equal to the width of the containing register field.",
)

stub(
    id="SCR 7.26",
    table="B.7",
    name="EnumeratedValueWithinWidth",
    single_doc_check=False,
    post_config=False,
    description="The enumeratedValue of an enumerationDefinition must fit within the enumerationDefinition width value.",
)

stub(
    id="SCR 7.27",
    table="B.7",
    name="registerAlignment",
    single_doc_check=False,
    post_config=False,
    description="For each register in an addressBlock with attribute misalignmentAllowed set to false it shall hold that (register bit offset % addressBlock width) + register size <= addressBlock width.",
)

stub(
    id="SCR 7.28",
    table="B.7",
    name="accessPolicyModeRefExists",
    single_doc_check=True,
    post_config=False,
    description="An accessPolicies element shall contain at most one accessPolicy element without modeRef elements.",
)

stub(
    id="SCR 7.29",
    table="B.7",
    name="fieldAccessPolicyModeRefExists",
    single_doc_check=True,
    post_config=False,
    description="A fieldAccessPolicies element shall contain at most one fieldAccessPolicy element without modeRef elements.",
)

stub(
    id="SCR 7.30",
    table="B.7",
    name="accessRestrictionModeRefExists",
    single_doc_check=True,
    post_config=False,
    description="An accessRestrictions element shall contain at most one accessRestriction element without modeRef elements.",
)

stub(
    id="SCR 7.31",
    table="B.7",
    name="RegisterFileWithinRegisterFile",
    single_doc_check=False,
    post_config=True,
    description="Any register file in a register file RF shall fall entirely within that register file RF, i.e., for every register file 0 <= registerFile.addressOffset <= RF.range - registerFileSize, where RF.range is the range of the register file RF and registerFileSize is the size of the register file in addressUnitBits. This is equal to dim[n-1]*dim[n]*...*dim[0]*stride, where dim is the maximum number of elements for each of n dimensions.",
)
