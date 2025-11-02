use crate::types::api::{SearchResponse, SearchResult};
use serde_json;
use std::error::Error;

pub fn format_search_results(data: &str) -> Result<String, Box<dyn Error>> {
    // Try to parse as SearchResponse first
    if let Ok(response) = serde_json::from_str::<SearchResponse>(data) {
        if let Some(results) = response.results {
            return format_results(&results);
        }
    }

    // Try to parse as single SearchResult
    if let Ok(result) = serde_json::from_str::<SearchResult>(data) {
        return format_results(&[result]);
    }

    // Try to parse as array of SearchResults
    if let Ok(results) = serde_json::from_str::<Vec<SearchResult>>(data) {
        return format_results(&results);
    }

    Err("Failed to parse search response".into())
}

fn format_results(results: &[SearchResult]) -> Result<String, Box<dyn Error>> {
    let mut output = String::new();

    for result in results {
        let mut content = result.content.clone();
        // Replace escaped newlines with actual newlines (matching Go implementation)
        content = content.replace("\\r\\n", "\r\n");
        content = content.replace("\\n", "\n");

        output.push_str(&format!("file: {}\n", result.file));
        output.push_str(&format!("startLine: {}\n", result.start_line));
        output.push_str(&format!("endLine: {}\n", result.end_line));
        output.push_str(&format!("score: {}\n", result.score));
        output.push_str(&format!("language: {}\n\n", result.language));
        output.push_str(&content);
        output.push_str("\n\n---\n");
    }

    Ok(output)
}