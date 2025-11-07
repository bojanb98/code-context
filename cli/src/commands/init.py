from config import load_config


async def init_command() -> None:

    from pydantic import HttpUrl
    from rich import print, print_json
    from rich.prompt import Confirm, IntPrompt, Prompt

    from config import DEFAULT_CONFIG_PATH, AppSettings, save_config

    config = AppSettings()

    if DEFAULT_CONFIG_PATH.exists():
        if not Confirm.ask("Configuration already exists. Overwrite?", default=True):
            print("Configuration initialization cancelled.")
            return

        config, _ = load_config()

    print("\n[bold]Qdrant Vector Database[/bold]")
    config.qdrant.url = HttpUrl(
        Prompt.ask("Qdrant host", default=str(config.qdrant.url))
    )

    if config.qdrant.url.host != "localhost":
        config.qdrant.api_key = Prompt.ask(
            "Qdrant API key", default=config.qdrant.api_key, password=True
        )

    # Embedding service configuration
    print("\n[bold]Embedding Service[/bold]")

    use_ollama = Confirm.ask("Use Ollama for embeddings?", default=True)

    if use_ollama:
        config.code_embedding.url = HttpUrl("http://localhost:11434/v1")
        config.code_embedding.api_key = "ollama"
        config.code_embedding.model = Prompt.ask(
            "Ollama embedding model", default=config.code_embedding.model
        )
        config.code_embedding.size = IntPrompt.ask(
            "Embedding size", default=config.code_embedding.size
        )
    else:
        config.code_embedding.url = HttpUrl(
            Prompt.ask("Embedding service URL", default=str(config.code_embedding.url))
        )
        config.code_embedding.api_key = Prompt.ask(
            "Embedding service API key",
            default=config.code_embedding.api_key,
            password=True,
        )
        config.code_embedding.model = Prompt.ask(
            "Embedding model", default=config.code_embedding.model
        )
        config.code_embedding.size = IntPrompt.ask(
            "Embedding size", default=config.code_embedding.size
        )

    use_docs = Confirm.ask(
        "Enable doc extraction? (may slightly slow down indexing)", default=True
    )
    use_explainer = Confirm.ask(
        "Enable code explanations? (may significantly slow down indexing)",
        default=False,
    )

    config.features.docs = use_docs
    config.features.explanation = use_explainer

    if use_docs:
        print("\n[bold]Doccummentation Embeddings[/bold]")
        config.doc_embedding.url = config.code_embedding.url
        config.doc_embedding.api_key = config.code_embedding.api_key
        config.doc_embedding.model = Prompt.ask(
            "Doc embedding model", default=config.doc_embedding.model
        )
        config.doc_embedding.size = IntPrompt.ask(
            "Explanation embedding size", default=config.doc_embedding.size
        )

    if use_explainer:
        print(
            "\n[bold]Code explanations (generated only if no docummentation extracted)[/bold]"
        )
        config.explainer.url = config.code_embedding.url
        config.explainer.api_key = config.code_embedding.api_key
        config.explainer.model = Prompt.ask(
            "Explainer model", default=config.explainer.model
        )

    print("\n[bold]Code Chunking[/bold]")
    config.chunking.chunk_size = IntPrompt.ask(
        "Chunk size (characters)", default=config.chunking.chunk_size
    )
    config.chunking.chunk_overlap = IntPrompt.ask(
        "Chunk overlap (characters)", default=config.chunking.chunk_overlap
    )

    save_config(config)
    print_json(config.model_dump_json())
