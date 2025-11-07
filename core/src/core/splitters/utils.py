from pathlib import Path

from tree_sitter_language_pack import SupportedLanguage

_LANGUAGE_EXTENSIONS: dict[str, SupportedLanguage] = {
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


SPLITTABLE_NODE_TYPES: dict[SupportedLanguage, list[str]] = {
    "javascript": [
        "function_declaration",
        "class_declaration",
        "method_definition",
        "arrow_function",
    ],
    "typescript": [
        "function_declaration",
        "class_declaration",
        "method_definition",
        "interface_declaration",
        "type_alias_declaration",
        "arrow_function",
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
    ],
    "go": [
        "function_declaration",
        "method_declaration",
        "type_declaration",
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


SUPPORTED_EXTENSIONS = set(_LANGUAGE_EXTENSIONS.keys())


def is_file_supported(path: Path) -> bool:
    if path.is_file():
        return path.suffix in SUPPORTED_EXTENSIONS
    return True
