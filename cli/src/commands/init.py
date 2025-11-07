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
        config.embedding.url = HttpUrl("http://localhost:11434/v1")
        config.embedding.api_key = "ollama"
        config.embedding.model = Prompt.ask(
            "Ollama embedding model", default=config.embedding.model
        )
        config.embedding.size = IntPrompt.ask(
            "Embedding size", default=config.embedding.size
        )
    else:
        config.embedding.url = HttpUrl(
            Prompt.ask("Embedding service URL", default=str(config.embedding.url))
        )
        config.embedding.api_key = Prompt.ask(
            "Embedding service API key", default=config.embedding.api_key, password=True
        )
        config.embedding.model = Prompt.ask(
            "Embedding model", default=config.embedding.model
        )
        config.embedding.size = IntPrompt.ask(
            "Embedding size", default=config.embedding.size
        )

    print("\n[bold]Explainer Service[/bold]")
    use_explainer = Confirm.ask(
        "Enable code explanations? (may slow down indexing)", default=False
    )
    config.explainer.enabled = use_explainer

    if use_explainer:
        config.explainer.url = config.embedding.url
        config.explainer.api_key = config.embedding.api_key
        config.explainer.model = Prompt.ask(
            "Explainer model", default=config.explainer.model
        )
        config.explainer.embedding.model = Prompt.ask(
            "Expalanations embedding model", default=config.explainer.embedding.model
        )
        config.explainer.embedding.size = IntPrompt.ask(
            "Explanation embedding size", default=config.explainer.embedding.size
        )

    # Chunking configuration
    print("\n[bold]Code Chunking[/bold]")
    config.chunking.chunk_size = IntPrompt.ask(
        "Chunk size (characters)", default=config.chunking.chunk_size
    )
    config.chunking.chunk_overlap = IntPrompt.ask(
        "Chunk overlap (characters)", default=config.chunking.chunk_overlap
    )

    save_config(config)
    print_json(config.model_dump_json())
