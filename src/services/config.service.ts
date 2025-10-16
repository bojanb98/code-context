import { promises as fs } from "node:fs";
import { join } from "node:path";
import { logger } from "../logger";

export interface ContextConfig {
  embeddingClass: string;
  embeddingUrl: string;
  embeddingModel: string;
  embeddingToken: string;
  milvusAddress: string;
  milvusToken: string;
}

export interface IgnoredPatterns {
  [projectPath: string]: string[];
}

export class ConfigService {
  private static readonly CONFIG_DIR = ".context-cli";
  private static readonly SETTINGS_FILE = "settings.json";
  private static readonly IGNORED_FILE = "ignored.json";

  private static getConfigDir(): string {
    const homeDir = process.env.HOME || process.env.USERPROFILE || "";
    return join(homeDir, ConfigService.CONFIG_DIR);
  }

  private static getSettingsPath(): string {
    return join(ConfigService.getConfigDir(), ConfigService.SETTINGS_FILE);
  }

  private static getIgnoredPatternsPath(): string {
    return join(ConfigService.getConfigDir(), ConfigService.IGNORED_FILE);
  }

  private static async ensureConfigDir(): Promise<void> {
    const configDir = ConfigService.getConfigDir();
    await fs.mkdir(configDir, { recursive: true });
  }

  private static handleFileError(error: unknown, filePath: string, operation: string): never {
    const message = error instanceof Error ? error.message : "Unknown error";
    logger.error(`Failed to ${operation} ${filePath}: ${message}`);
    throw new Error(`Failed to ${operation} ${filePath}: ${message}`);
  }

  static getDefaultConfig(): ContextConfig {
    return {
      embeddingClass: "ollama",
      embeddingUrl: "http://localhost:11434",
      embeddingModel: "vuongnguyen2212/CodeRankEmbed",
      embeddingToken: "",
      milvusAddress: "localhost:19530",
      milvusToken: "",
    };
  }

  static async loadConfig(): Promise<ContextConfig> {
    const settingsPath = ConfigService.getSettingsPath();

    try {
      await fs.access(settingsPath);
      const configText = await fs.readFile(settingsPath, "utf-8");
      const fileConfig = JSON.parse(configText);

      const envConfig: Partial<ContextConfig> = {
        milvusAddress: process.env.MILVUS_ADDRESS,
        milvusToken: process.env.MILVUS_TOKEN,
        embeddingClass: process.env.EMBEDDING_CLASS,
        embeddingUrl: process.env.EMBEDDING_URL,
        embeddingModel: process.env.EMBEDDING_MODEL,
        embeddingToken: process.env.EMBEDDING_TOKEN,
      };

      const mergedConfig = {
        ...ConfigService.getDefaultConfig(),
        ...fileConfig,
        ...envConfig,
      };

      return ConfigService.validateConfig(mergedConfig);
    } catch (error: any) {
      if (error.code === "ENOENT") {
        logger.info("No configuration found, creating default configuration");
        return await ConfigService.saveConfig(ConfigService.getDefaultConfig());
      } else {
        ConfigService.handleFileError(error, settingsPath, "load config from");
      }
    }
  }

  static async saveConfig(config: ContextConfig): Promise<ContextConfig> {
    const settingsPath = ConfigService.getSettingsPath();

    try {
      await ConfigService.ensureConfigDir();
      const validatedConfig = ConfigService.validateConfig(config);
      await fs.writeFile(settingsPath, JSON.stringify(validatedConfig, null, 2));
      logger.info(`Configuration saved to ${settingsPath}`);
      return validatedConfig;
    } catch (error) {
      ConfigService.handleFileError(error, settingsPath, "save config to");
    }
  }

  static async loadIgnoredPatterns(): Promise<IgnoredPatterns> {
    const ignoredPath = ConfigService.getIgnoredPatternsPath();

    try {
      await fs.access(ignoredPath);
      const configText = await fs.readFile(ignoredPath, "utf-8");
      return JSON.parse(configText) as IgnoredPatterns;
    } catch (error: any) {
      if (error.code === "ENOENT") {
        return await ConfigService.saveIgnoredPatterns({});
      } else {
        ConfigService.handleFileError(error, ignoredPath, "load ignored patterns from");
      }
    }
  }

  static async saveIgnoredPatterns(patterns: IgnoredPatterns): Promise<IgnoredPatterns> {
    const ignoredPath = ConfigService.getIgnoredPatternsPath();

    try {
      await ConfigService.ensureConfigDir();
      await fs.writeFile(ignoredPath, JSON.stringify(patterns, null, 2));
      logger.info(`Ignored patterns saved to ${ignoredPath}`);
      return patterns;
    } catch (error) {
      ConfigService.handleFileError(error, ignoredPath, "save ignored patterns to");
    }
  }

  private static validateConfig(config: Partial<ContextConfig>): ContextConfig {
    return {
      embeddingClass: config.embeddingClass || "ollama",
      embeddingUrl: config.embeddingUrl || "http://localhost:11434",
      embeddingModel: config.embeddingModel || "vuongnguyen2212/CodeRankEmbed",
      embeddingToken: config.embeddingToken || "",
      milvusAddress: config.milvusAddress || "localhost:19530",
      milvusToken: config.milvusToken || "",
    };
  }
}