import {
  Context,
  OpenAIEmbedding,
  OllamaEmbedding,
  MilvusVectorDatabase,
} from "@zilliz/claude-context-core";
import { logger } from "./logger";
import {
  ConfigService,
  ContextConfig,
  IgnoredPatterns,
} from "./services/config.service";

export { ContextConfig, IgnoredPatterns };

export async function getConfig(): Promise<ContextConfig> {
  return await ConfigService.loadConfig();
}

export async function saveConfig(
  config: ContextConfig,
): Promise<ContextConfig> {
  return await ConfigService.saveConfig(config);
}

export async function getIgnoredPatterns(): Promise<IgnoredPatterns> {
  return await ConfigService.loadIgnoredPatterns();
}

export async function saveIgnoredPatterns(
  patterns: IgnoredPatterns,
): Promise<IgnoredPatterns> {
  return await ConfigService.saveIgnoredPatterns(patterns);
}

export async function getContext(
  additionalIgnorePatterns?: string[],
): Promise<Context> {
  const config = await getConfig();

  logger.debug(
    `Initializing context with ${config.embeddingClass} embedding provider`,
  );
  logger.debug(`Milvus address: ${config.milvusAddress}`);

  try {
    // Initialize embedding provider
    let embedding;
    if (config.embeddingClass === "openai") {
      logger.debug(`Using OpenAI embedding model: ${config.embeddingModel}`);
      embedding = new OpenAIEmbedding({
        apiKey: config.embeddingToken!,
        model: config.embeddingModel!,
      });
    } else {
      logger.debug(`Using Ollama embedding model: ${config.embeddingModel}`);
      logger.debug(`Ollama base URL: ${config.embeddingUrl}`);
      embedding = new OllamaEmbedding({
        model: config.embeddingModel!,
        host: config.embeddingUrl!,
      });
    }

    // Initialize vector database
    logger.debug("Connecting to Milvus vector database");
    const vectorDatabase = new MilvusVectorDatabase({
      address: config.milvusAddress,
      token: config.milvusToken,
    });

    // Get project-specific ignored patterns from global ignored.json
    const currentWorkingDir = process.cwd();
    const ignoredPatterns = await getIgnoredPatterns();
    const projectSpecificPatterns = ignoredPatterns[currentWorkingDir] || [];

    // Combine all ignore patterns
    const allIgnorePatterns = [
      ...projectSpecificPatterns,
      ...(additionalIgnorePatterns || []),
    ];

    logger.debug(`Using ignore patterns: ${allIgnorePatterns.join(", ")}`);

    // Create context instance
    logger.debug("Creating context instance");
    const context = new Context({
      embedding,
      vectorDatabase,
      ignorePatterns: allIgnorePatterns,
    });

    logger.debug("Context initialized successfully");

    return context;
  } catch (error) {
    logger.error(
      `Failed to initialize context: ${error instanceof Error ? error.message : "Unknown error"}`,
    );
    throw new Error(
      `Failed to initialize context: ${error instanceof Error ? error.message : "Unknown error"}`,
    );
  }
}
