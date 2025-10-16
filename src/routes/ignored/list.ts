import { getIgnoredPatterns } from "../../context";
import { logger } from "../../logger";

export async function listIgnoredRoutes(query: any): Promise<any> {
  const { path } = query;

  try {
    const currentWorkingDir = process.cwd();
    const targetProject = path || currentWorkingDir;

    logger.debug(`Listing ignored patterns for project: ${targetProject}`);

    const ignoredPatterns = await getIgnoredPatterns();

    if (path) {
      // List patterns for specified project
      const patterns = ignoredPatterns[path] || [];
      logger.info(`Ignored patterns for project: ${path}`);

      return {
        patterns,
        projectPath: path,
        totalPatterns: patterns.length,
      };
    } else {
      // List patterns for current directory and show all configured projects
      const currentPatterns = ignoredPatterns[currentWorkingDir] || [];

      logger.info(
        `Ignored patterns for current project (${currentWorkingDir})`,
      );

      // Show all configured projects
      const allProjects = Object.keys(ignoredPatterns);
      const projectsSummary = allProjects.map((project) => ({
        path: project,
        count: ignoredPatterns[project].length,
      }));

      return {
        currentProject: {
          path: currentWorkingDir,
          patterns: currentPatterns,
          totalPatterns: currentPatterns.length,
        },
        allProjects: projectsSummary,
      };
    }
  } catch (error) {
    logger.error(
      `Error listing ignored patterns: ${error instanceof Error ? error.message : "Unknown error"}`,
    );

    throw error;
  }
}

