import { Elysia, t } from "elysia";
import { getConfig } from "../../context";
import { logger } from "../../logger";

export const configRoutes = new Elysia({
  prefix: "/api/config",
  tags: ["config"],
  name: "Config",
})
  .get(
    "/",
    async () => {
      try {
        const config = await getConfig();

        logger.info("Configuration requested");

        return {
          embeddingClass: config.embeddingClass,
          embeddingUrl: config.embeddingUrl,
          embeddingModel: config.embeddingModel,
          embeddingToken: config.embeddingToken ? "***" : "not set",
          milvusAddress: config.milvusAddress,
          milvusToken: config.milvusToken ? "***" : "not set",
        };
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Unknown error";
        logger.error(`Error loading configuration: ${errorMessage}`);

        throw error;
      }
    },
    {
      response: t.Object({
        embeddingClass: t.String(),
        embeddingUrl: t.String(),
        embeddingModel: t.String(),
        embeddingToken: t.String(),
        milvusAddress: t.String(),
        milvusToken: t.String(),
      }),
    },
  )
  .onError(({ error, code }) => {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";
    logger.error(`Config routes error: ${errorMessage}`);

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

