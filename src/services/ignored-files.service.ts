import { getIgnoredPatterns, saveIgnoredPatterns } from "../context";
import { logger } from "../logger";

export class IgnoredFilesService {
  /**
   * Add an ignored pattern to a project
   */
  static async addPattern(
    path: string,
    pattern: string,
  ): Promise<{
    path: string;
    pattern: string;
    totalPatterns: number;
    added: boolean;
  }> {
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
        path,
        pattern,
        totalPatterns: ignoredPatterns[path].length,
        added: true,
      };
    } else {
      logger.warn(`Pattern "${pattern}" already exists for project ${path}`);

      return {
        path,
        pattern,
        totalPatterns: ignoredPatterns[path].length,
        added: false,
      };
    }
  }

  static async removePattern(
    path: string,
    pattern: string,
  ): Promise<{
    path: string;
    pattern: string;
    totalPatterns: number;
    removed: boolean;
  }> {
    logger.debug(`Removing ignored pattern "${pattern}" from project: ${path}`);

    const ignoredPatterns = await getIgnoredPatterns();

    if (!ignoredPatterns[path]) {
      logger.warn(`No ignored patterns configured for project ${path}`);

      return {
        path,
        pattern,
        totalPatterns: 0,
        removed: false,
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
        path,
        pattern,
        totalPatterns: patterns.length,
        removed: true,
      };
    } else {
      logger.warn(`Pattern "${pattern}" not found for project ${path}`);

      return {
        path,
        pattern,
        totalPatterns: patterns.length,
        removed: false,
      };
    }
  }

  /**
   * List ignored patterns for a project or all projects
   */
  static async listPatterns(path?: string): Promise<{
    currentProject?: {
      path: string;
      patterns: string[];
      totalPatterns: number;
    };
    allProjects?: Array<{
      path: string;
      count: number;
    }>;
    patterns?: string[];
    projectPath?: string;
    totalPatterns?: number;
  }> {
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
  }
}
