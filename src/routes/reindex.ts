import { getContext } from "../context";
import { logger } from "../logger";

export async function reindexRoutes(body: any): Promise<any> {
  const { path } = body;

  try {
    logger.debug(`Reindexing codebase at: ${path}`);

    const context = await getContext();

    logger.debug("Reindexing by change (detecting modified files)");

    await context.reindexByChange(path);

    logger.info("Reindexing completed");

    return {
      message: "Successfully reindexed codebase",
    };
  } catch (error) {
    logger.error(
      `Error reindexing codebase: ${error instanceof Error ? error.message : "Unknown error"}`,
    );

    throw error;
  }
}

