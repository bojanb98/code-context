async def init_command() -> None:

    from pydantic import HttpUrl
    from rich import print, print_json
    from rich.prompt import Confirm, IntPrompt, Prompt

    from cli.config import DEFAULT_CONFIG_PATH, AppSettings, save_config

    if DEFAULT_CONFIG_PATH.exists():
        if not Confirm.ask(
            "Configuration already exists. Overwrite?",
        ):
            print("Configuration initialization cancelled.")
            return

    config = AppSettings()

    print("\n[bold]Qdrant Vector Database[/bold]")
    config.qdrant.url = HttpUrl(Prompt.ask("Qdrant host", default=config.qdrant.url))

    if config.qdrant.url.host != "localhost":
        config.qdrant.api_key = Prompt.ask(
            "Qdrant API key", default=None, password=True
        )

    # Embedding service configuration
    print("\n[bold]Embedding Service[/bold]")

    use_ollama = Confirm.ask("Use Ollama for embeddings?")

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
            Prompt.ask("Embedding service URL", default="https://api.openai.com/v1")
        )
        config.embedding.api_key = Prompt.ask(
            "Embedding service API key", password=True
        )
        config.embedding.model = Prompt.ask(
            "Embedding model", default=config.embedding.model
        )
        config.embedding.size = IntPrompt.ask(
            "Embedding size", default=config.embedding.size
        )

    print("\n[bold]Explainer Service[/bold]")
    use_explainer = Confirm.ask("Enable code explanations?")
    config.explainer.enabled = use_explainer

    if use_explainer:
        config.explainer.url = config.embedding.url
        config.explainer.api_key = config.embedding.api_key
        config.explainer.model = Prompt.ask(
            "Explainer model", default=config.explainer.model
        )
        config.explainer.embedding_model = Prompt.ask(
            "Expalanations embedding model", default=config.explainer.embedding_model
        )
        config.explainer.embedding_size = IntPrompt.ask(
            "Explanation embedding size", default=768
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
