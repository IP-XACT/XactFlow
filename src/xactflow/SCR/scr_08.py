"""IEEE 1685-2022 Annex B, Table B.8: Memory maps (10 rules, SCR 8.1-8.10).

None of these are implemented yet; every rule is registered via stub() so it is tracked and
discoverable through SCR.all_rules().
"""

from __future__ import annotations

from .registry import stub

stub(
    id="SCR 8.1",
    table="B.8",
    name="BlockWidthCondition",
    single_doc_check=False,
    post_config=False,
    description="The width of an address block included in a memory map or memory map definition shall be a multiple of the memory map's addressUnitBits.",
)

stub(
    id="SCR 8.2",
    table="B.8",
    name="NoSubspaceInParallelBank",
    single_doc_check=True,
    post_config=False,
    description="Neither a parallel bank nor banks within a parallel bank shall contain subspace maps.",
)

stub(
    id="SCR 8.3",
    table="B.8",
    name="addressBlockContent",
    single_doc_check=True,
    post_config=False,
    description="A register or register file cannot appear in an addressBlock with a usage of reserved.",
)

stub(
    id="SCR 8.4",
    table="B.8",
    name="BlockOverlap",
    single_doc_check=False,
    post_config=True,
    description=(
        "Two addressBlocks in the same memoryMap shall not overlap, i.e. no address block "
        "shall have a baseAddress that falls within the address range of another block in "
        "the same memoryMap. The address range of an address block is [baseAddress, "
        "baseAddress + addressBlockSize - 1]."
    ),
)

stub(
    id="SCR 8.5",
    table="B.8",
    name="virtualRegisterContent",
    single_doc_check=True,
    post_config=False,
    description="The registerDefinitionGroup in a virtual register shall contain only typeIdentifier, size, and field elements.",
)

stub(
    id="SCR 8.6",
    table="B.8",
    name="virtualAlternateRegisterContent",
    single_doc_check=True,
    post_config=False,
    description="When an alternate register is a child of a virtual register, the alternateRegisterDefinitionGroup shall contain only typeIdentifier and field elements.",
)

stub(
    id="SCR 8.7",
    table="B.8",
    name="virtualFieldContent",
    single_doc_check=True,
    post_config=False,
    description="If a field is a child of a virtual register, the fieldData group shall contain only enumeratedValue and writeValueConstraint elements.",
)

stub(
    id="SCR 8.8",
    table="B.8",
    name="StrideRangeRelationship",
    single_doc_check=False,
    post_config=False,
    description="The stride of an addressBlock or registerFile element shall be greater than or equal to the range of the address block or register file.",
)

stub(
    id="SCR 8.9",
    table="B.8",
    name="StrideSizeRelationship",
    single_doc_check=False,
    post_config=False,
    description="The stride of a register element shall be greater than or equal to the size of the register.",
)

stub(
    id="SCR 8.10",
    table="B.8",
    name="StrideBitwidthRelationship",
    single_doc_check=True,
    post_config=False,
    description="The bitStride of a registerField element shall be greater than or equal to the bitWidth of the field.",
)
