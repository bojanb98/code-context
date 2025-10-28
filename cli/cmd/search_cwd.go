package cmd

import (
	"os"
	"strconv"

	"github.com/spf13/cobra"
)

var searchCwdCmd = &cobra.Command{
	Use:   "search-cwd <query> [limit] [extensions]",
	Short: "Search indexed code in current directory",
	Long:  `Search indexed code in the current working directory with a query.`,
	Args:  cobra.RangeArgs(1, 3),
	RunE:  runSearchCwd,
}

func runSearchCwd(cmd *cobra.Command, args []string) error {
	cwd, err := os.Getwd()
	if err != nil {
		return err
	}

	searchArgs := []string{cwd}
	searchArgs = append(searchArgs, args...)

	limit := 5
	if len(args) >= 2 {
		var err error
		limit, err = strconv.Atoi(args[1])
		if err != nil {
			return err
		}
	}

	if len(args) == 1 {
		searchArgs = append(searchArgs, strconv.Itoa(limit))
	} else if len(args) >= 2 {
		searchArgs = append(searchArgs, args[1])
		if len(args) >= 3 {
			searchArgs = append(searchArgs, args[2])
		}
	}

	return searchCmd.RunE(cmd, searchArgs)
}