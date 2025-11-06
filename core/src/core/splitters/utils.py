from pathlib import Path

from tree_sitter_language_pack import SupportedLanguage

LANGUAGE_EXTENSIONS: dict[str, SupportedLanguage] = {
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".py": "python",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
}

SUPPORTED_EXTENSIONS = set(LANGUAGE_EXTENSIONS.keys())

SPLITTABLE_NODE_TYPES: dict[SupportedLanguage, list[str]] = {
    "javascript": [
        "function_declaration",
        "arrow_function",
        "class_declaration",
        "method_definition",
        "export_statement",
    ],
    "typescript": [
        "function_declaration",
        "arrow_function",
        "class_declaration",
        "method_definition",
        "export_statement",
        "interface_declaration",
        "type_alias_declaration",
    ],
    "python": [
        "function_definition",
        "class_definition",
        "decorated_definition",
        "async_function_definition",
    ],
    "java": [
        "method_declaration",
        "class_declaration",
        "interface_declaration",
        "constructor_declaration",
    ],
    "cpp": [
        "function_definition",
        "class_specifier",
        "namespace_definition",
        "declaration",
    ],
    "go": [
        "function_declaration",
        "method_declaration",
        "type_declaration",
        "var_declaration",
        "const_declaration",
    ],
    "rust": [
        "function_item",
        "impl_item",
        "struct_item",
        "enum_item",
        "trait_item",
        "mod_item",
    ],
    "csharp": [
        "method_declaration",
        "class_declaration",
        "interface_declaration",
        "struct_declaration",
        "enum_declaration",
    ],
    "scala": [
        "method_declaration",
        "class_declaration",
        "interface_declaration",
        "constructor_declaration",
    ],
}


def is_file_supported(path: Path) -> bool:
    if path.is_file():
        return path.suffix in SUPPORTED_EXTENSIONS
    return True
