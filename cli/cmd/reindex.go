package cmd

import (
	"fmt"

	"github.com/claude-code-extensions/cli/internal/http"
	"github.com/claude-code-extensions/cli/internal/path"
	"github.com/spf13/cobra"
)

var reindexCmd = &cobra.Command{
	Use:   "reindex <path>",
	Short: "Reindex a code directory",
	Long:  `Reindex a code directory at the specified path for searching.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runReindex,
}

func runReindex(cmd *cobra.Command, args []string) error {
	pathArg := args[0]

	absPath, err := path.ToAbsolute(pathArg)
	if err != nil {
		return fmt.Errorf("invalid path: %w", err)
	}

	client := http.NewClient()

	request := http.IndexPathRequest{
		Path: http.EscapePath(absPath),
	}

	response, err := client.Post("/api/index/reindex", request)
	if err != nil {
		return fmt.Errorf("reindex request failed: %w", err)
	}

	fmt.Print(string(response))
	return nil
}