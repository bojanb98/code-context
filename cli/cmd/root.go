package cmd

import (
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "code",
	Short: "CLI for code indexing and search",
	Long: `Code is a CLI tool for indexing and searching codebases.
It provides commands to index, reindex, search, and unindex code.`,
}

func Execute() error {
	return rootCmd.Execute()
}

func init() {
	rootCmd.AddCommand(indexCmd)
	rootCmd.AddCommand(reindexCmd)
	rootCmd.AddCommand(searchCmd)
	rootCmd.AddCommand(unindexCmd)
}
