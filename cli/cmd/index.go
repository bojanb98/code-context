package cmd

import (
	"fmt"

	"github.com/claude-code-extensions/cli/internal/http"
	"github.com/spf13/cobra"
)

var indexCmd = &cobra.Command{
	Use:   "index <path>",
	Short: "Index a code directory",
	Long:  `Index a code directory at the specified path for searching.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runIndex,
}

func runIndex(cmd *cobra.Command, args []string) error {
	path := args[0]
	client := http.NewClient()

	request := http.IndexPathRequest{
		Path: http.EscapePath(path),
	}

	response, err := client.Post("/api/index/", request)
	if err != nil {
		return fmt.Errorf("index request failed: %w", err)
	}

	fmt.Print(string(response))
	return nil
}
