use crate::client::http::HttpClient;
use crate::format::search::format_search_results;
use crate::types::api::{IndexPathRequest, SearchParams};
use crate::utils::path::to_absolute;
use std::error::Error;

pub async fn execute_index(client: &HttpClient, path: String, force: bool) -> Result<(), Box<dyn Error>> {
    let abs_path = to_absolute(&path)?;
    let request = IndexPathRequest {
        path: abs_path,
        force,
    };

    let response = client.post("/api/index/", &request).await?;
    println!("{}", response);
    Ok(())
}

pub async fn execute_search(
    client: &HttpClient,
    path: String,
    query: String,
    limit: u32,
    extensions: Option<String>,
) -> Result<(), Box<dyn Error>> {
    let abs_path = to_absolute(&path)?;
    let params = SearchParams {
        path: abs_path,
        query,
        limit,
        extensions,
    };

    let response = client.get("/api/search/", &params).await?;
    let formatted = format_search_results(&response)?;
    print!("{}", formatted);
    Ok(())
}

pub async fn execute_unindex(client: &HttpClient, path: String) -> Result<(), Box<dyn Error>> {
    let abs_path = to_absolute(&path)?;
    let request = IndexPathRequest {
        path: abs_path,
        force: false, // force is not used for unindex
    };

    let response = client.delete("/api/index/", &request).await?;
    println!("{}", response);
    Ok(())
}