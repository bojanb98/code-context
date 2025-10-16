import { getIgnoredPatterns, saveIgnoredPatterns } from "../../context";
import { logger } from "../../logger";

export async function removeIgnoredRoutes(body: any): Promise<any> {
  const { path, pattern } = body;

  try {
    logger.debug(`Removing ignored pattern "${pattern}" from project: ${path}`);

    const ignoredPatterns = await getIgnoredPatterns();

    if (!ignoredPatterns[path]) {
      logger.warn(`No ignored patterns configured for project ${path}`);

      return {
        message: `No ignored patterns configured for project ${path}`,
        path,
        pattern,
        totalPatterns: 0,
      };
    }

    // Remove the pattern if it exists
    const patterns = ignoredPatterns[path];
    const index = patterns.indexOf(pattern);
    if (index > -1) {
      patterns.splice(index, 1);
      await saveIgnoredPatterns(ignoredPatterns);
      logger.info(`Removed pattern "${pattern}" from project ${path}`);

      return {
        message: `Successfully removed pattern "${pattern}" from project ${path}`,
        path,
        pattern,
        totalPatterns: patterns.length,
      };
    } else {
      logger.warn(`Pattern "${pattern}" not found for project ${path}`);

      return {
        message: `Pattern "${pattern}" not found for project ${path}`,
        path,
        pattern,
        totalPatterns: patterns.length,
      };
    }
  } catch (error) {
    logger.error(
      `Error removing ignored pattern: ${error instanceof Error ? error.message : "Unknown error"}`,
    );

    throw error;
  }
}

