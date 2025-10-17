import { Elysia, t } from "elysia";
import { getContext } from "../../context";
import { logger } from "../../logger";

export const searchRoutes = new Elysia({
  prefix: "/api/search",
  tags: ["search"],
  name: "Search",
})
  .get(
    "/",
    async ({ query }) => {
      const { path, query: searchQuery, limit = 5, extensions } = query;

      try {
        logger.debug(`Searching for: "${searchQuery}"`);
        logger.debug(`Path: ${path}`);

        const context = await getContext();
        const results = await context.semanticSearch(path, searchQuery, limit);

        if (results.length === 0) {
          logger.info("No results found.");
          return {
            results: [],
            query: searchQuery,
            path,
            limit,
            totalResults: 0,
          };
        }

        // Transform results to match expected format
        const transformedResults = results.map((result) => ({
          file: result.relativePath,
          startLine: result.startLine,
          endLine: result.endLine,
          score: result.score,
          language: result.language,
          content: result.content,
        }));

        logger.info(`Found ${results.length} result(s)`);
        return {
          results: transformedResults,
          query: searchQuery,
          path,
          limit,
          totalResults: results.length,
        };
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Unknown error";
        logger.error(`Error searching codebase: ${errorMessage}`);

        throw error;
      }
    },
    {
      query: t.Object({
        path: t.String({
          description: "Path to the codebase to search in",
        }),
        query: t.String({
          description: "Search query",
        }),
        limit: t.Optional(
          t.Numeric({
            minimum: 1,
            maximum: 100,
            default: 5,
            description: "Maximum number of results to return",
          }),
        ),
        extensions: t.Optional(
          t.Array(
            t.String({
              description: "File extensions to filter results by",
            }),
          ),
        ),
      }),
      response: t.Object({
        results: t.Array(
          t.Object({
            file: t.String(),
            startLine: t.Numeric(),
            endLine: t.Numeric(),
            score: t.Numeric(),
            language: t.String(),
            content: t.String(),
          }),
        ),
        query: t.String(),
        path: t.String(),
        limit: t.Numeric(),
        totalResults: t.Numeric(),
      }),
    },
  )
  .onError(({ error, code }) => {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";
    logger.error(`Search routes error: ${errorMessage}`);

    if (code === "VALIDATION") {
      return {
        error: "Invalid request parameters",
        details: errorMessage,
      };
    }

    return {
      error: errorMessage,
    };
  });

