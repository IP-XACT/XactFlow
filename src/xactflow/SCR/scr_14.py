"""IEEE 1685-2022 Annex B, Table B.14: Expressions (32 rules, SCR 14.1-14.32).

None of these are implemented yet; every rule is registered via stub() so it is tracked and
discoverable through SCR.all_rules(). Almost all of them need real IP-XACT expression
evaluation as SystemVerilog, which ipxact-compiler deliberately leaves unevaluated
(Expression = str) and XactFlow does not implement yet either.
"""

from __future__ import annotations

from .registry import stub

stub(
    id="SCR 14.1",
    table="B.14",
    name="complexTiedValueExpression",
    single_doc_check=False,
    post_config=True,
    description=(
        "A value specified as a complexTiedValueExpression shall be resolved to string "
        "values \"default\" or \"open\" or to an unsigned bit vector as specified by the "
        "SystemVerilog specification, where the vector size is determined by the port slice "
        "width in the ad hoc connection."
    ),
)

stub(
    id="SCR 14.2",
    table="B.14",
    name="unsignedLongintExpression",
    single_doc_check=True,
    post_config=False,
    description="A value specified as an unsignedLongintExpression shall be resolved to an unsigned longint as specified by the SystemVerilog specification.",
)

stub(
    id="SCR 14.3",
    table="B.14",
    name="unsignedPositiveLongintExpression",
    single_doc_check=True,
    post_config=False,
    description="A value specified as an unsignedPositiveLongintExpression shall be resolved to an unsigned longint with a value greater than 0 as specified by the SystemVerilog specification.",
)

stub(
    id="SCR 14.4",
    table="B.14",
    name="signedLongintExpression",
    single_doc_check=True,
    post_config=False,
    description="A value specified as a signedLongintExpression shall be resolved to a signed longint as specified by the SystemVerilog specification.",
)

stub(
    id="SCR 14.5",
    table="B.14",
    name="unsignedIntExpression",
    single_doc_check=True,
    post_config=False,
    description="A value specified as an unsignedIntExpression shall be resolved to an unsigned int as specified by the SystemVerilog specification.",
)

stub(
    id="SCR 14.6",
    table="B.14",
    name="unsignedPositiveIntExpression",
    single_doc_check=True,
    post_config=False,
    description="A value specified as an unsignedPositiveIntExpression shall be resolved to an unsigned int with a value greater than 0 as specified by the SystemVerilog specification.",
)

stub(
    id="SCR 14.7",
    table="B.14",
    name="realExpression",
    single_doc_check=True,
    post_config=False,
    description="A value specified as a realExpression shall resolve to a real as specified by the SystemVerilog specification.",
)

stub(
    id="SCR 14.8",
    table="B.14",
    name="stringExpression",
    single_doc_check=True,
    post_config=False,
    description="A value specified as a stringExpression shall be resolved to a string as specified by the SystemVerilog specification.",
)

stub(
    id="SCR 14.9",
    table="B.14",
    name="unsignedBitExpression",
    single_doc_check=True,
    post_config=False,
    description="A value specified as an unsignedBitExpression shall be resolved to an unsigned bit as specified by the SystemVerilog specification.",
)

stub(
    id="SCR 14.10",
    table="B.14",
    name="unsignedBitVectorExpression",
    single_doc_check=True,
    post_config=False,
    description="A value specified as an unsignedBitVectorExpression shall be resolved to an unsigned bit vector as specified by the SystemVerilog specification, where the vector size is determined by an external value (e.g. field size for reset-value).",
)

stub(
    id="SCR 14.11",
    table="B.14",
    name="parameterExpression",
    single_doc_check=True,
    post_config=False,
    description="A parameter expression (complexBaseExpression) shall be resolved to the SystemVerilog type and sign specified for the specific parameter.",
)

stub(
    id="SCR 14.12",
    table="B.14",
    name="sformatfArgCount",
    single_doc_check=True,
    post_config=False,
    description="When $sformatf() is used within an accessHandle element, the invocation must have at least as many arguments beyond the format argument as the format has escapes which require an argument.",
)

stub(
    id="SCR 14.13",
    table="B.14",
    name="sformatfArgType",
    single_doc_check=True,
    post_config=False,
    description="When $sformatf() is used within an accessHandle element, the type of an argument must match the format escape's allowed arguments.",
)

stub(
    id="SCR 14.14",
    table="B.14",
    name="EscapeSequences",
    single_doc_check=True,
    post_config=False,
    description="The escape sequences (not functions) $ipxact_index_value and $ipxact_parameter_value can only be used within values of displayName, description, and shortDescription elements.",
)

stub(
    id="SCR 14.15",
    table="B.14",
    name="ipxact_index_value",
    single_doc_check=True,
    post_config=False,
    description="The function $ipxact_index_value() can only be used within values of pathSegment elements.",
)

stub(
    id="SCR 14.16",
    table="B.14",
    name="ipxact_field_value",
    single_doc_check=True,
    post_config=False,
    description="The function $ipxact_field_value() can only be used within values of mode condition elements.",
)

stub(
    id="SCR 14.17",
    table="B.14",
    name="ipxact_port_value",
    single_doc_check=True,
    post_config=False,
    description="The function $ipxact_port_value() can only be used within values of mode condition elements.",
)

stub(
    id="SCR 14.18",
    table="B.14",
    name="ipxact_mode_condition",
    single_doc_check=True,
    post_config=False,
    description="The function $ipxact_mode_condition() can only be used within values of mode condition elements.",
)

stub(
    id="SCR 14.19",
    table="B.14",
    name="ipxact_packetfield_value",
    single_doc_check=True,
    post_config=False,
    description="The function $ipxact_packetfield_value() can only be used within values of packetField width elements.",
)

stub(
    id="SCR 14.20",
    table="B.14",
    name="ipxact_absdefport_value",
    single_doc_check=True,
    post_config=False,
    description="The function $ipxact_absdefport_value() can only be used within values of packetField width elements.",
)

stub(
    id="SCR 14.21",
    table="B.14",
    name="IndexValueIndexVarExists",
    single_doc_check=False,
    post_config=False,
    description="When using $ipxact_index_value(<indexVar>) in a string expression or escape sequence, the referenced <indexVar> must exist as ipxact:dim/@indexVar within the object hierarchy of the containing memoryMap.",
)

stub(
    id="SCR 14.22",
    table="B.14",
    name="ModeValueMustExist",
    single_doc_check=False,
    post_config=False,
    description="When using $ipxact_mode_condition(<mode>) in a string expression, the referenced <mode> must exist as a visible mode within the containing component.",
)

stub(
    id="SCR 14.23",
    table="B.14",
    name="ParameterValueParameterExists",
    single_doc_check=False,
    post_config=False,
    description="When using escape sequence $ipxact_parameter_value(<parameter-id>), the referenced parameter with id==<parameter-id> must be defined within the scope of the containing top level element.",
)

stub(
    id="SCR 14.24",
    table="B.14",
    name="indexUniqueness",
    single_doc_check=False,
    post_config=False,
    description="The value of the indexVar attribute on a dim element must be unique within its scope.",
)

stub(
    id="SCR 14.25",
    table="B.14",
    name="qualifiedExpression",
    single_doc_check=True,
    post_config=True,
    description="The value of a qualifiedExpression in a defaultValue of a wire port shall resolve to an unsignedBitExpression, unsignedBitVectorExpression, realExpression, or realVectorExpression depending on whether the port is digital/analog and scalar/vector.",
)

stub(
    id="SCR 14.26",
    table="B.14",
    name="FieldValueFieldSliceExists",
    single_doc_check=False,
    post_config=False,
    description="When using $ipxact_fieldslice_value(<fieldSliceRef>) in a string of a mode condition, the referenced <fieldSliceRef> must exist as ipxact:fieldSlice in the encapsulating mode element.",
)

stub(
    id="SCR 14.27",
    table="B.14",
    name="PortValuePortSliceExists",
    single_doc_check=False,
    post_config=False,
    description="When using $ipxact_port_value(<portSliceRef>) in a string expression of a mode condition, the referenced <portSliceRef> must exist as ipxact:portSlice in the encapsulating mode element.",
)

stub(
    id="SCR 14.28",
    table="B.14",
    name="PortValueAbsDefPortExists",
    single_doc_check=False,
    post_config=False,
    description="When using $ipxact_absdefport_value(<portRef>) in a packetField, the referenced <portRef> must exist as ipxact:port of the containing abstraction definition.",
)

stub(
    id="SCR 14.29",
    table="B.14",
    name="PacketFieldValuePacketFieldExists",
    single_doc_check=True,
    post_config=False,
    description="When using $ipxact_packetfield_value(<packetFieldRef>) in a packetField width, the referenced <packetFieldRef> must exist as ipxact:packetField within the object hierarchy of the containing ipxact:packet.",
)

stub(
    id="SCR 14.30",
    table="B.14",
    name="unresolvedStringExpressionValid",
    single_doc_check=True,
    post_config=False,
    description="Expressions of type unresolvedStringExpression shall be valid IP-XACT expressions even though they cannot be evaluated.",
)

stub(
    id="SCR 14.31",
    table="B.14",
    name="unresolvedUnsignedBitExpressionValid",
    single_doc_check=True,
    post_config=False,
    description="Expressions of type unresolvedUnsignedBitExpression shall be valid IP-XACT expressions even though they cannot be evaluated.",
)

stub(
    id="SCR 14.32",
    table="B.14",
    name="unresolvedUnsignedPositiveIntExpressionValid",
    single_doc_check=True,
    post_config=False,
    description="Expressions of type unresolvedUnsignedPositiveIntExpression shall be valid IP-XACT expressions even though they cannot be evaluated.",
)
