package cmd

import (
	"fmt"
	"strconv"

	"github.com/claude-code-extensions/cli/internal/format"
	"github.com/claude-code-extensions/cli/internal/http"
	"github.com/spf13/cobra"
)

var searchCmd = &cobra.Command{
	Use:   "search <path> <query> [limit] [extensions]",
	Short: "Search indexed code",
	Long:  `Search indexed code at the specified path with a query.`,
	Args:  cobra.RangeArgs(2, 4),
	RunE:  runSearch,
}

func runSearch(cmd *cobra.Command, args []string) error {
	path := args[0]
	query := args[1]

	limit := 5
	if len(args) >= 3 {
		var err error
		limit, err = strconv.Atoi(args[2])
		if err != nil {
			return fmt.Errorf("invalid limit value: %s", args[2])
		}
	}

	extensions := ""
	if len(args) >= 4 {
		extensions = args[3]
	}

	client := http.NewClient()

	params := map[string]string{
		"path":  path,
		"query": query,
		"limit": strconv.Itoa(limit),
	}

	if extensions != "" {
		params["extensions"] = extensions
	}

	response, err := client.Get("/api/search/", params)
	if err != nil {
		return fmt.Errorf("search request failed: %w", err)
	}

	formatted, err := format.FormatSearchResults(response)
	if err != nil {
		return fmt.Errorf("failed to format search results: %w", err)
	}

	fmt.Print(formatted)
	return nil
}