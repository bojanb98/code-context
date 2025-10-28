package cmd

import (
	"fmt"

	"github.com/claude-code-extensions/cli/internal/http"
	"github.com/claude-code-extensions/cli/internal/path"
	"github.com/spf13/cobra"
)

var unindexCmd = &cobra.Command{
	Use:   "unindex <path>",
	Short: "Unindex a code directory",
	Long:  `Remove a code directory at the specified path from the index.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runUnindex,
}

func runUnindex(cmd *cobra.Command, args []string) error {
	pathArg := args[0]

	absPath, err := path.ToAbsolute(pathArg)
	if err != nil {
		return fmt.Errorf("invalid path: %w", err)
	}

	client := http.NewClient()

	request := http.IndexPathRequest{
		Path: http.EscapePath(absPath),
	}

	response, err := client.Delete("/api/index/", request)
	if err != nil {
		return fmt.Errorf("unindex request failed: %w", err)
	}

	fmt.Print(string(response))
	return nil
}