package format

import (
	"encoding/json"
	"fmt"
	"strings"
)

type SearchResult struct {
	File      string  `json:"file"`
	StartLine int     `json:"startLine"`
	EndLine   int     `json:"endLine"`
	Score     float64 `json:"score"`
	Language  string  `json:"language"`
	Content   string  `json:"content"`
}

type SearchResponse struct {
	Results []SearchResult `json:"results,omitempty"`
}

func FormatSearchResults(data []byte) (string, error) {
	var response SearchResponse
	var results []SearchResult

	if err := json.Unmarshal(data, &response); err == nil && len(response.Results) > 0 {
		results = response.Results
	} else {
		var singleResult SearchResult
		if err := json.Unmarshal(data, &singleResult); err == nil {
			results = []SearchResult{singleResult}
		} else {
			var multipleResults []SearchResult
			if err := json.Unmarshal(data, &multipleResults); err == nil {
				results = multipleResults
			} else {
				return "", fmt.Errorf("failed to parse search response")
			}
		}
	}

	var output strings.Builder
	for _, result := range results {
		content := result.Content
		content = strings.ReplaceAll(content, "\\r\\n", "\r\n")
		content = strings.ReplaceAll(content, "\\n", "\n")

		output.WriteString(fmt.Sprintf("file: %s\n", result.File))
		output.WriteString(fmt.Sprintf("startLine: %d\n", result.StartLine))
		output.WriteString(fmt.Sprintf("endLine: %d\n", result.EndLine))
		output.WriteString(fmt.Sprintf("score: %f\n", result.Score))
		output.WriteString(fmt.Sprintf("language: %s\n\n", result.Language))
		output.WriteString(content)
		output.WriteString("\n\n---\n")
	}

	return output.String(), nil
}
