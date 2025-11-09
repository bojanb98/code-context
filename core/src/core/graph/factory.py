from collections.abc import Mapping
from typing import Type

from tree_sitter_language_pack import SupportedLanguage

from .builders import DefaultGraphBuilder, GraphBuilder, PythonGraphBuilder

BuilderClass = Type[GraphBuilder]

_LANGUAGE_BUILDERS: Mapping[SupportedLanguage, BuilderClass] = {
    "python": PythonGraphBuilder,
}


def get_builder(language: SupportedLanguage) -> GraphBuilder:
    """Return a graph builder tuned for the requested language."""
    builder_cls = _LANGUAGE_BUILDERS.get(language, DefaultGraphBuilder)
    return builder_cls()
