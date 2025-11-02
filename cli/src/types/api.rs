use crate::utils::path::escape_path;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Debug)]
pub struct IndexPathRequest {
    #[serde(serialize_with = "serialize_path")]
    pub path: String,
    pub force: bool,
}

fn serialize_path<S>(path: &str, serializer: S) -> Result<S::Ok, S::Error>
where
    S: serde::Serializer,
{
    let escaped = escape_path(path);
    serializer.serialize_str(&escaped)
}

#[derive(Serialize, Debug)]
pub struct SearchParams {
    pub path: String,
    pub query: String,
    pub limit: u32,
    pub extensions: Option<String>,
}

#[derive(Deserialize, Debug)]
pub struct SearchResult {
    pub file: String,
    #[serde(rename = "startLine")]
    pub start_line: i32,
    #[serde(rename = "endLine")]
    pub end_line: i32,
    pub score: f64,
    pub language: String,
    pub content: String,
}

#[derive(Deserialize, Debug)]
pub struct SearchResponse {
    pub results: Option<Vec<SearchResult>>,
}
