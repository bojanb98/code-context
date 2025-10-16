import { Elysia, t } from "elysia";
import { getContext } from "../../context";
import { logger } from "../../logger";

export const indexRoutes = new Elysia({ prefix: "/api/index" })
  .post(
    "/",
    async ({ body }) => {
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
          path,
          force,
          indexedFiles: stats.indexedFiles,
          totalChunks: stats.totalChunks,
        };
      } catch (error) {
        logger.error(
          `Error indexing codebase: ${error instanceof Error ? error.message : "Unknown error"}`,
        );

        throw error;
      }
    },
    {
      body: t.Object({
        path: t.String({
          description: "Path to the codebase to index",
        }),
        force: t.Optional(
          t.Boolean({
            default: false,
            description: "Force reindexing even if already indexed",
          }),
        ),
      }),
      response: t.Object({
        path: t.String(),
        force: t.Boolean(),
        indexedFiles: t.Numeric(),
        totalChunks: t.Numeric(),
      }),
    },
  )
  .delete(
    "/",
    async ({ body }) => {
      const { path } = body;

      try {
        logger.debug(`Clearing index for codebase at: ${path}`);

        const context = await getContext();
        await context.clearIndex(path);

        logger.info("Successfully cleared index");

        return {
          path,
        };
      } catch (error) {
        logger.error(
          `Error clearing index: ${error instanceof Error ? error.message : "Unknown error"}`,
        );

        throw error;
      }
    },
    {
      body: t.Object({
        path: t.String({
          description: "Path to the codebase to clear index for",
        }),
      }),
      response: t.Object({
        path: t.String(),
      }),
    },
  )
  .post(
    "/reindex",
    async ({ body }) => {
      const { path } = body;

      try {
        logger.debug(`Reindexing codebase at: ${path}`);

        const context = await getContext();

        logger.debug("Reindexing by change (detecting modified files)");

        await context.reindexByChange(path);

        logger.info("Reindexing completed");

        return {
          path,
        };
      } catch (error) {
        logger.error(
          `Error reindexing codebase: ${error instanceof Error ? error.message : "Unknown error"}`,
        );

        throw error;
      }
    },
    {
      body: t.Object({
        path: t.String({
          description: "Path to the codebase to reindex",
        }),
      }),
      response: t.Object({
        path: t.String(),
      }),
    },
  )
  .onError(({ error, code }) => {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    logger.error(`Index routes error: ${errorMessage}`);

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