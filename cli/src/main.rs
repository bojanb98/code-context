use clap::{Parser, Subcommand};
use client::http::HttpClient;

mod cli;
mod client;
mod types;
mod format;
mod utils;

#[derive(Parser)]
#[command(name = "code")]
#[command(about = "CLI for code indexing and search", long_about = "Code is a CLI tool for indexing and searching codebases. It provides commands to index, reindex, search, and unindex code.")]
#[command(version)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    #[command(about = "Index a code directory", long_about = "Index a code directory at the specified path for searching.")]
    Index {
        #[arg(help = "Directory path to index")]
        path: String,
        #[arg(short, long, help = "Force reindexing even if already indexed")]
        force: bool,
    },
    #[command(about = "Search indexed code", long_about = "Search indexed code at the specified path with a query.")]
    Search {
        #[arg(help = "Directory path to search in")]
        path: String,
        #[arg(help = "Search query string")]
        query: String,
        #[arg(help = "Maximum number of results", default_value = "5")]
        limit: u32,
        #[arg(help = "File extensions to filter (e.g., \".go,.js\")")]
        extensions: Option<String>,
    },
    #[command(about = "Unindex a code directory", long_about = "Remove a code directory at the specified path from the index.")]
    Unindex {
        #[arg(help = "Directory path to remove from index")]
        path: String,
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
        Commands::Search { path, query, limit, extensions } => {
            cli::commands::execute_search(&client, path, query, limit, extensions).await?;
        }
        Commands::Unindex { path } => {
            cli::commands::execute_unindex(&client, path).await?;
        }
    }

    Ok(())
}