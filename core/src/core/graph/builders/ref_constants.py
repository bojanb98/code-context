IDENTIFIER_NODE_TYPES = {
    "identifier",
    "type_identifier",
    "field_identifier",
    "property_identifier",
    "shorthand_property_identifier",
    "attribute_identifier",
}

CALL_NODE_TYPES = {
    "call_expression",
    "call",
    "function_call",
    "method_invocation",
    "decorated_call_expression",
}

TYPE_REFERENCE_NODE_TYPES = {
    "scoped_type_identifier",
    "qualified_type_identifier",
    "generic_type",
    "object_creation_expression",
    "new_expression",
}

MEMBER_NODE_TYPES = {
    "attribute",
    "member_expression",
    "field_expression",
    "scoped_field_expression",
    "optional_field_expression",
    "optional_member_expression",
}

SELF_RECEIVER_NAMES = {"self", "this", "cls", "super"}

PARAMETER_PARENT_TYPES = set(
    (
        "parameters parameter_list formal_parameters lambda_parameters "
        "typed_parameter default_parameter self_parameter required_parameter "
        "posonly_parameters kwonly_parameters"
    ).split()
)

ASSIGNMENT_PARENT_TYPES = set(
    (
        "assignment assignment_expression augmented_assignment_expression "
        "assignment_statement variable_assignment variable_declarator "
        "lexical_declaration const_declaration let_declaration "
        "short_var_declaration"
    ).split()
)

ALIAS_PARENT_TYPES = ASSIGNMENT_PARENT_TYPES | {
    "variable_declaration",
    "equals_value_clause",
}

MEMBER_ATTRIBUTE_FIELDS = {"attribute", "property", "name", "field"}

PATTERN_PARENT_TYPES = set(
    (
        "pattern tuple_pattern list_pattern destructuring_pattern object_pattern "
        "array_pattern binding_pattern structured_binding_declaration"
    ).split()
)

LOOP_TARGET_PARENT_TYPES = set(
    (
        "for_statement for_in_clause for_in_statement enhanced_for_statement "
        "for_range_loop foreach_statement"
    ).split()
)

CATCH_PARENT_TYPES = set(
    ("catch_clause catch_formal_parameter catch_declaration").split()
)

OWNER_NODE_TYPES = set(
    (
        "class_definition class_declaration interface_declaration "
        "struct_declaration enum_declaration impl_item trait_item "
        "object_definition namespace_definition"
    ).split()
)
IMPORT_ALIAS_PARENT_TYPES = {
    "aliased_import",
    "import_specifier",
    "import_clause",
    "namespace_import",
    "import_as_clause",
    "import_clause_entry",
    "imported_binding",
    "use_clause",
    "use_as_clause",
}
