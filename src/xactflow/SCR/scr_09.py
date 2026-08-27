"""IEEE 1685-2022 Annex B, Table B.9: Addressing (10 rules, SCR 9.1-9.10).

None of these are implemented yet; every rule is registered via stub() so it is tracked and
discoverable through SCR.all_rules().
"""

from __future__ import annotations

from .registry import stub

stub(
    id="SCR 9.1",
    table="B.9",
    name="AddressableInitiatorHasRef",
    single_doc_check=True,
    post_config=False,
    description="A non-hierarchical addressable initiator bus interface shall have an addressSpaceRef subelement.",
)

stub(
    id="SCR 9.2",
    table="B.9",
    name="AddressableTargetHasMapOrBridge",
    single_doc_check=True,
    post_config=False,
    description="A non-hierarchical addressable target bus interface shall have a memoryMapRef subelement or one or more bridge subelements referencing addressable initiator bus interfaces.",
)

stub(
    id="SCR 9.3",
    table="B.9",
    name="BitSteeringRestriction",
    single_doc_check=True,
    post_config=False,
    description="bitSteering is not allowed in mirrored-initiator, system, or mirrored-system interface modes.",
)

stub(
    id="SCR 9.4",
    table="B.9",
    name="ChannelDataWidthRestriction",
    single_doc_check=True,
    post_config=False,
    description="Data widths in a channel shall all be a power-of-2 multiple of their bitsInLau.",
)

stub(
    id="SCR 9.5",
    table="B.9",
    name="BitsInLauRestriction",
    single_doc_check=True,
    post_config=False,
    description="bitsInLau in a channel shall all be a power-of-2 multiple of the smallest bitsInLau.",
)

stub(
    id="SCR 9.6",
    table="B.9",
    name="SegmentCondition",
    single_doc_check=True,
    post_config=False,
    description="For each segment within an addressSpace, everything between offsetAddress and offsetAddress + range - 1 shall be contained within the range of that addressSpace.",
)

stub(
    id="SCR 9.7",
    table="B.9",
    name="SegmentRefExists",
    single_doc_check=True,
    post_config=False,
    description="The segmentRef shall reference an existing segment of the addressSpace in the initiator referenced by the initiatorRef.",
)

stub(
    id="SCR 9.8",
    table="B.9",
    name="indirectDataField",
    single_doc_check=True,
    post_config=False,
    description="The field referenced as indirectData shall not be part of the memory map referenced by the memoryMapRef.",
)

stub(
    id="SCR 9.9",
    table="B.9",
    name="indirectAddressRefField",
    single_doc_check=True,
    post_config=False,
    description="The field referenced as indirectAddress shall not be part of the memory map referenced by the memoryMapRef.",
)

stub(
    id="SCR 9.10",
    table="B.9",
    name="indirectAddressRefFieldAccess",
    single_doc_check=True,
    post_config=False,
    description="The field referenced as indirectAddress shall not have an access-type of read-only, read-writeOnce, writeOnce, or no-access.",
)
