from cyclopts import App

from commands import (
    drop_command,
    index_command,
    init_command,
    mcp_command,
    search_command,
)


def create_app() -> App:
    return App(
        name="code-context",
        help="Semantic code search CLI - Index and search your codebase using AI",
        version="1.3.0",
    )


app = create_app()

app.command(init_command, name="init")
app.command(index_command, name="index")
app.command(search_command, name="search")
app.command(drop_command, name="drop")
app.command(mcp_command, name="mcp")


@app.default
async def default_command() -> None:
    from rich import print

    print("Code Context CLI - Semantic code search")
    print("Use 'code-context --help' to see available commands.")
    print("Get started with 'code-context init' to configure the CLI.")


if __name__ == "__main__":
    app()
