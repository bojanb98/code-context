import { getIgnoredPatterns, saveIgnoredPatterns } from "../../context";
import { logger } from "../../logger";

export async function addIgnoredRoutes(body: any): Promise<any> {
  const { path, pattern } = body;

  try {
    logger.debug(`Adding ignored pattern "${pattern}" to project: ${path}`);

    const ignoredPatterns = await getIgnoredPatterns();

    // Initialize patterns array for this project if it doesn't exist
    if (!ignoredPatterns[path]) {
      ignoredPatterns[path] = [];
    }

    // Add the pattern if it's not already there
    if (!ignoredPatterns[path].includes(pattern)) {
      ignoredPatterns[path].push(pattern);
      await saveIgnoredPatterns(ignoredPatterns);
      logger.info(`Added pattern "${pattern}" to project ${path}`);

      return {
        message: `Successfully added pattern "${pattern}" to project ${path}`,
        path,
        pattern,
        totalPatterns: ignoredPatterns[path].length,
      };
    } else {
      logger.warn(`Pattern "${pattern}" already exists for project ${path}`);

      return {
        message: `Pattern "${pattern}" already exists for project ${path}`,
        path,
        pattern,
        totalPatterns: ignoredPatterns[path].length,
      };
    }
  } catch (error) {
    logger.error(
      `Error adding ignored pattern: ${error instanceof Error ? error.message : "Unknown error"}`,
    );

    throw error;
  }
}

