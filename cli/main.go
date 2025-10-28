package main

import (
	"github.com/claude-code-extensions/cli/cmd"
	"os"
)

func main() {
	if err := cmd.Execute(); err != nil {
		os.Exit(1)
	}
}
