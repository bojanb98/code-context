use reqwest;
use serde::Serialize;
use std::error::Error;
use std::time::Duration;

const BASE_URL: &str = "http://localhost:19531";

pub struct HttpClient {
    client: reqwest::Client,
}

impl HttpClient {
    pub fn new() -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");

        Self { client }
    }

    pub async fn post<T: Serialize>(&self, path: &str, body: &T) -> Result<String, Box<dyn Error>> {
        let url = format!("{}{}", BASE_URL, path);
        let response = self
            .client
            .post(&url)
            .json(body)
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(format!("Request failed with status: {}", response.status()).into());
        }

        let text = response.text().await?;
        Ok(text)
    }

    pub async fn get<T: Serialize>(&self, path: &str, params: &T) -> Result<String, Box<dyn Error>> {
        let url = format!("{}{}", BASE_URL, path);

        // Convert params to query string using serde_json
        let params_json = serde_json::to_value(params)?;
        let mut query_params = Vec::new();

        if let serde_json::Value::Object(map) = params_json {
            for (key, value) in map {
                if let serde_json::Value::String(s) = value {
                    query_params.push(format!("{}={}", key, urlencoding::encode(&s)));
                } else {
                    query_params.push(format!("{}={}", key, urlencoding::encode(&value.to_string())));
                }
            }
        }

        let full_url = if !query_params.is_empty() {
            format!("{}?{}", url, query_params.join("&"))
        } else {
            url
        };

        let response = self.client.get(&full_url).send().await?;

        if !response.status().is_success() {
            return Err(format!("Request failed with status: {}", response.status()).into());
        }

        let text = response.text().await?;
        Ok(text)
    }

    pub async fn delete<T: Serialize>(&self, path: &str, body: &T) -> Result<String, Box<dyn Error>> {
        let url = format!("{}{}", BASE_URL, path);
        let response = self
            .client
            .delete(&url)
            .json(body)
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(format!("Request failed with status: {}", response.status()).into());
        }

        let text = response.text().await?;
        Ok(text)
    }
}