import { getContext } from "../context";
import { logger } from "../logger";
import { t } from "elysia";

export async function searchRoutes(query: any): Promise<any> {
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
    };
  } catch (error) {
    logger.error(
      `Error searching codebase: ${error instanceof Error ? error.message : "Unknown error"}`,
    );

    throw error;
  }
}

