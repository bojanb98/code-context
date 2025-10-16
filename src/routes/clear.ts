import { getContext } from "../context";
import { logger } from "../logger";

export async function clearRoutes(body: any): Promise<any> {
  const { path } = body;

  try {
    logger.debug(`Clearing index for codebase at: ${path}`);

    const context = await getContext();
    await context.clearIndex(path);

    logger.info("Successfully cleared index");

    return {
      message: "Successfully cleared index",
    };
  } catch (error) {
    logger.error(
      `Error clearing index: ${error instanceof Error ? error.message : "Unknown error"}`,
    );

    throw error;
  }
}

