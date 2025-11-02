use clap::{Parser, Subcommand};
use client::http::HttpClient;

mod cli;
mod client;
mod format;
mod types;
mod utils;

#[derive(Parser)]
#[command(name = "code")]
#[command(about = "CLI for code indexing and search")]
#[command(version)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    #[command(about = "Index a code directory")]
    Index {
        #[arg(help = "Directory path to index (defaults to current directory)")]
        path: Option<String>,
        #[arg(short, long, help = "Force reindexing even if already indexed")]
        force: bool,
    },
    #[command(about = "Search indexed code")]
    Search {
        #[arg(help = "Search query string")]
        query: String,
        #[arg(help = "Directory path to search in (defaults to current directory)")]
        path: Option<String>,
        #[arg(help = "Maximum number of results", default_value = "5")]
        limit: u32,
        #[arg(help = "File extensions to filter (e.g., \".go,.js\")")]
        extensions: Option<String>,
    },
    #[command(about = "Remove a code directory from the index")]
    Drop {
        #[arg(help = "Directory path to remove from index (defaults to current directory)")]
        path: Option<String>,
    },
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    let client = HttpClient::new();

    match cli.command {
        Commands::Index { path, force } => {
            cli::commands::execute_index(&client, path, force).await?;
        }
        Commands::Search {
            query,
            path,
            limit,
            extensions,
        } => {
            cli::commands::execute_search(&client, path, query, limit, extensions).await?;
        }
        Commands::Drop { path } => {
            cli::commands::execute_drop(&client, path).await?;
        }
    }

    Ok(())
}
