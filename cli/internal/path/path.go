package path

import (
	"fmt"
	"path/filepath"
)

// ToAbsolute converts a relative path to an absolute path.
// If the path is already absolute, it returns the path as-is.
// Returns an error if the path cannot be converted to absolute.
func ToAbsolute(path string) (string, error) {
	if path == "" {
		return "", fmt.Errorf("path cannot be empty")
	}

	absPath, err := filepath.Abs(path)
	if err != nil {
		return "", fmt.Errorf("failed to convert path to absolute: %w", err)
	}

	return absPath, nil
}