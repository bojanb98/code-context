import { getContext } from "../context";
import { logger } from "../logger";

export async function indexRoutes(body: any): Promise<any> {
  const { path, force = false } = body;

  try {
    logger.debug(`Indexing codebase at: ${path}`);

    const context = await getContext();
    const stats = await context.indexCodebase(path, (progress) => {
      logger.debug(`${progress.phase} - ${progress.percentage}%`);
    });

    logger.info(
      `Successfully indexed ${stats.indexedFiles} files with ${stats.totalChunks} chunks`,
    );

    return {
      message: "Successfully indexed codebase",
      indexedFiles: stats.indexedFiles,
      totalChunks: stats.totalChunks,
    };
  } catch (error) {
    logger.error(
      `Error indexing codebase: ${error instanceof Error ? error.message : "Unknown error"}`,
    );

    throw error;
  }
}

