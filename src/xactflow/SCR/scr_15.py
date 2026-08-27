"""IEEE 1685-2022 Annex B, Table B.15: Access handles (3 rules, SCR 15.1-15.3).

None of these are implemented yet; every rule is registered via stub() so it is tracked and
discoverable through SCR.all_rules().
"""

from __future__ import annotations

from .registry import stub

stub(
    id="SCR 15.1",
    table="B.15",
    name="accessHandleIndex",
    single_doc_check=True,
    post_config=True,
    description="The indices specified for the accessHandle should reference an index within the bounds specified by the array element when specified for a port.",
)

stub(
    id="SCR 15.2",
    table="B.15",
    name="accessHandleSlice",
    single_doc_check=True,
    post_config=True,
    description="It is not allowed to specify more than one accessHandle/slices/slice element, and it is not allowed to specify a slice/range on an addressBlock with a usage of register or reserved.",
)

stub(
    id="SCR 15.3",
    table="B.15",
    name="ClearBoxElementRefExists",
    single_doc_check=True,
    post_config=False,
    description="A clearboxElementRef, which references a clearboxElement with a clearboxType of pin, shall have a pathName that is a port in the containing description.",
)
