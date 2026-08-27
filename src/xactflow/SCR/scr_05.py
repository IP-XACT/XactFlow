"""IEEE 1685-2022 Annex B, Table B.5: Configurable elements (28 rules, SCR 5.1-5.28).

None of these are implemented yet; every rule is registered via stub() so it is tracked and
discoverable through SCR.all_rules().
"""

from __future__ import annotations

from .registry import stub

stub(
    id="SCR 5.1",
    table="B.5",
    name="expressionFieldValue",
    single_doc_check=True,
    post_config=False,
    description=(
        "The value of a field that allows expressions shall be an expression and shall "
        "reference only parameters in the document using their parameterId."
    ),
)

stub(
    id="SCR 5.2",
    table="B.5",
    name="parameterIdRequired",
    single_doc_check=True,
    post_config=False,
    description="A parameterId attribute is required in any element with a resolve attribute value of user or generated.",
)

stub(
    id="SCR 5.3",
    table="B.5",
    name="componentInstanceConfigurableElementReferences",
    single_doc_check=False,
    post_config=False,
    description=(
        "configurableElementValue elements within componentInstance elements shall reference "
        "only configurable elements that exist in the component referenced by the enclosing "
        "componentInstance element, excluding those in a componentInstantiation or "
        "designConfigurationInstantiation. The referenceId attribute value shall match the "
        "parameterId attribute value of some configurable element of the component."
    ),
)

stub(
    id="SCR 5.4",
    table="B.5",
    name="configElementRefCondition",
    single_doc_check=False,
    post_config=False,
    description="configurableElementValue elements shall reference only configurable elements.",
)

stub(
    id="SCR 5.5",
    table="B.5",
    name="configurableElementMin",
    single_doc_check=False,
    post_config=False,
    description=(
        "If a configurableElementValue element references an element with a type attribute "
        "that does not specify a string and contains a minimum attribute, the value of the "
        "configurableElementValue element shall be greater than or equal to the specified "
        "value of the minimum attribute."
    ),
)

stub(
    id="SCR 5.6",
    table="B.5",
    name="configurableElementMax",
    single_doc_check=False,
    post_config=False,
    description=(
        "If a configurableElementValue element references an element with a type attribute "
        "that does not specify a string and contains a maximum attribute, the value of the "
        "configurableElementValue subelement shall be less than or equal to the specified "
        "value of the maximum attribute."
    ),
)

stub(
    id="SCR 5.7",
    table="B.5",
    name="ConfigElementChoiceExists",
    single_doc_check=False,
    post_config=False,
    description=(
        "If a configurableElementValue element references an element with a choiceRef "
        "attribute, the value for the configurableElementValue subelement shall be one of "
        "the values listed in the choice element referenced by the choiceRef attribute."
    ),
)

stub(
    id="SCR 5.8",
    table="B.5",
    name="designConfigurationInstantiationConfigurableElementReferences",
    single_doc_check=False,
    post_config=False,
    description=(
        "configurableElementValue elements within designConfigurationInstantiation elements "
        "shall reference only configurable elements that exist in the designConfiguration "
        "referenced by the enclosing designConfigurationInstantiation element; the "
        "parameterId attribute value shall match the parameterId attribute value of some "
        "configurable element of the design configuration."
    ),
)

stub(
    id="SCR 5.9",
    table="B.5",
    name="viewConfigurationConfigurableElementReferences",
    single_doc_check=False,
    post_config=False,
    description=(
        "configurableElementValue elements within viewConfiguration elements shall reference "
        "only configurable elements that exist in the componentInstantiation or "
        "designConfigurationInstantiation referenced in the component view referenced by the "
        "enclosing view element; the referenceId attribute value shall match the parameterId "
        "attribute value of some configurable element of the component."
    ),
)

stub(
    id="SCR 5.10",
    table="B.5",
    name="generatorChainConfigurableElementReferences",
    single_doc_check=False,
    post_config=False,
    description=(
        "configurableElementValue elements within generatorChainConfiguration elements in "
        "design configuration documents shall reference only configurable elements that "
        "exist in the generator chain referenced by the generatorChainRef element."
    ),
)

stub(
    id="SCR 5.11",
    table="B.5",
    name="abstractorConfigurableElementReferences",
    single_doc_check=False,
    post_config=False,
    description=(
        "configurableElementValue elements within interconnectionConfiguration elements "
        "shall reference only configurable elements that exist in the abstractor referenced "
        "by the enclosing abstractorRef element."
    ),
)

stub(
    id="SCR 5.12",
    table="B.5",
    name="parameterImplicitCast",
    single_doc_check=False,
    post_config=False,
    description=(
        "A parameter's value or a configurable element's value shall be implicitly converted "
        "to the type and length specified by the type attribute and the vectors and arrays "
        "elements, resulting in an error when the value cannot be cast to the specified type, "
        "e.g. string to any other types and any other types to string."
    ),
)

stub(
    id="SCR 5.13",
    table="B.5",
    name="expressionsMinMax",
    single_doc_check=True,
    post_config=False,
    description="Expressions are bound by the values specified by the minimum and maximum attributes.",
)

stub(
    id="SCR 5.14",
    table="B.5",
    name="componentInstantiationParameterReferences",
    single_doc_check=True,
    post_config=False,
    description="Parameters inside a componentInstantiation cannot be referenced by expressions outside that componentInstantiation.",
)

stub(
    id="SCR 5.15",
    table="B.5",
    name="designConfigurationInstantiationParameterReferences",
    single_doc_check=True,
    post_config=False,
    description="Parameters inside a designConfigurationInstantiation cannot be referenced by expressions outside that designConfigurationInstantiation.",
)

stub(
    id="SCR 5.16",
    table="B.5",
    name="parameterInitializations",
    single_doc_check=True,
    post_config=False,
    description="The value of a parameter shall resolve to its indicated type.",
)

stub(
    id="SCR 5.17",
    table="B.5",
    name="expressionSyntax",
    single_doc_check=True,
    post_config=False,
    description="Expressions shall follow the SystemVerilog syntax.",
)

stub(
    id="SCR 5.18",
    table="B.5",
    name="expressionIDsExist",
    single_doc_check=True,
    post_config=False,
    description="Any ID used in an expression shall reference an existing parameterID.",
)

stub(
    id="SCR 5.19",
    table="B.5",
    name="expressionNonCircular",
    single_doc_check=True,
    post_config=False,
    description="Evaluation of an expression shall not lead to circular referencing.",
)

stub(
    id="SCR 5.20",
    table="B.5",
    name="vectorDeclaration",
    single_doc_check=True,
    post_config=False,
    description="Vectors shall be specified only on parameters with a type of bit.",
)

stub(
    id="SCR 5.21",
    table="B.5",
    name="arrayDeclaration",
    single_doc_check=True,
    post_config=False,
    description=(
        "Array parameters shall be fully initialized; it shall be an error if the size of the "
        "array as determined by the default value differs from the size the array specified "
        "by the arrays elements."
    ),
)

stub(
    id="SCR 5.22",
    table="B.5",
    name="arrayConfiguration",
    single_doc_check=True,
    post_config=False,
    description=(
        "Arrays shall be fully overridden when configured; it shall be an error if the size "
        "of the array resulting from the values specified in the configurable element "
        "differs from the size of the array specified by the arrays elements."
    ),
)

stub(
    id="SCR 5.23",
    table="B.5",
    name="designInstantiationConfigurableElementReferences",
    single_doc_check=False,
    post_config=False,
    description=(
        "configurableElementValue elements within designInstantiation elements in component "
        "documents shall reference only configurable elements that exist in the design "
        "referenced by the enclosing designInstantiation element."
    ),
)

stub(
    id="SCR 5.24",
    table="B.5",
    name="busTypeConfigurableElementReferences",
    single_doc_check=False,
    post_config=False,
    description=(
        "configurableElementValue elements within busType elements shall reference only "
        "configurable elements that exist in the bus definition referenced by the enclosing "
        "busType element."
    ),
)

stub(
    id="SCR 5.25",
    table="B.5",
    name="abstractionTypeConfigurableElementReferences",
    single_doc_check=False,
    post_config=False,
    description=(
        "configurableElementValue elements within abstractionType elements shall reference "
        "only configurable elements that exist in the abstraction definition referenced by "
        "the enclosing abstractionType element."
    ),
)

stub(
    id="SCR 5.26",
    table="B.5",
    name="assertionValidity",
    single_doc_check=False,
    post_config=True,
    description="The value of an assertion shall evaluate to true.",
)

stub(
    id="SCR 5.27",
    table="B.5",
    name="typeDefinitionsRefConfigurableElementReferences",
    single_doc_check=False,
    post_config=False,
    description=(
        "configurableElementValue elements within typeDefinitionsRef elements shall "
        "reference only configurable elements that exist in the typeDefinitions referenced "
        "by the enclosing typeDefinitionsRef element."
    ),
)

stub(
    id="SCR 5.28",
    table="B.5",
    name="noRefIdToImmediate",
    single_doc_check=False,
    post_config=False,
    description="configurableElementValue attribute referenceId shall not reference configurable elements with a resolve attribute value of immediate.",
)
