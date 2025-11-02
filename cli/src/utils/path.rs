use std::error::Error;
use std::path::Path;

/// Converts a relative path to an absolute path.
/// If the path is already absolute, it returns the path as-is.
/// Returns an error if the path cannot be converted to absolute.
pub fn to_absolute(path: &str) -> Result<String, Box<dyn Error>> {
    if path.is_empty() {
        return Err("path cannot be empty".into());
    }

    let path_buf = Path::new(path);
    let abs_path = if path_buf.is_absolute() {
        path_buf.to_path_buf()
    } else {
        std::env::current_dir()?.join(path_buf)
    };

    // Convert to string and normalize path separators
    let abs_path_str = abs_path
        .to_str()
        .ok_or("Invalid path characters")?
        .to_string();

    Ok(abs_path_str)
}

/// Escapes a path for JSON serialization (matches Go implementation)
pub fn escape_path(path: &str) -> String {
    path.replace('\\', "\\\\").replace('\"', "\\\"")
}
