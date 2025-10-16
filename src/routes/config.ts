import { getConfig } from "../context";
import { logger } from "../logger";

export async function configRoutes(): Promise<any> {
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
    logger.error(
      `Error loading configuration: ${error instanceof Error ? error.message : "Unknown error"}`,
    );

    throw error;
  }
}

