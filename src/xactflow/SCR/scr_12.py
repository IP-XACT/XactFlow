"""IEEE 1685-2022 Annex B, Table B.12: Constraints (9 rules, SCR 12.1-12.9).

None of these are implemented yet; every rule is registered via stub() so it is tracked and
discoverable through SCR.all_rules().
"""

from __future__ import annotations

from .registry import stub

stub(
    id="SCR 12.1",
    table="B.12",
    name="NoOutputDriveConstraint",
    single_doc_check=True,
    post_config=False,
    description="A component wire port with direction out shall not have a drive constraint.",
)

stub(
    id="SCR 12.2",
    table="B.12",
    name="NoInputLoadConstraint",
    single_doc_check=True,
    post_config=False,
    description="A component wire port with a direction in shall not have a load constraint.",
)

stub(
    id="SCR 12.3",
    table="B.12",
    name="NoOutputDriveModeConstraint",
    single_doc_check=True,
    post_config=False,
    description="An onInitiator, onTarget, or onSystem element of a wire port with direction out shall not contain a drive constraint within its modeConstraint element.",
)

stub(
    id="SCR 12.4",
    table="B.12",
    name="NoInputLoadModeConstraint",
    single_doc_check=True,
    post_config=False,
    description="An onInitiator, onTarget, or onSystem element of a wire port with direction in shall not contain a load constraint within its modeConstraint element.",
)

stub(
    id="SCR 12.5",
    table="B.12",
    name="NoOutputLoadMirroredModeConstraint",
    single_doc_check=True,
    post_config=False,
    description="An onInitiator, onTarget, or onSystem element of a wire port with direction out shall not contain a load constraint within its mirroredModeConstraint element.",
)

stub(
    id="SCR 12.6",
    table="B.12",
    name="NoInputDriveMirroredModeConstraint",
    single_doc_check=True,
    post_config=False,
    description="An onInitiator, onTarget, or onSystem element of a wire port with direction in shall not contain a drive constraint within its mirroredModeConstraint element.",
)

stub(
    id="SCR 12.7",
    table="B.12",
    name="ConstraintClockExists",
    single_doc_check=True,
    post_config=False,
    description="The clockName in a timing constraint of a component port shall be the clockName of a clockDriver or otherClockDriver element within the component, unless none are present, in which case it shall be the name of another component port.",
)

stub(
    id="SCR 12.8",
    table="B.12",
    name="ConstraintClockLogicalPortExists",
    single_doc_check=True,
    post_config=False,
    description="The clockName in a timing constraint of a port within an abstraction definition shall be the name of another port of the abstraction definition; that referenced port shall have an isClock subelement.",
)

stub(
    id="SCR 12.9",
    table="B.12",
    name="DriverSingleBitCondition",
    single_doc_check=True,
    post_config=False,
    description="Only a scalar port or single-bit bussed port may have a clockDriver or a singleShotDriver subelement.",
)
