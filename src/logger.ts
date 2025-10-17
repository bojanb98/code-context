import winston from "winston";

// Simple winston logger with console only
const winstonLogger = winston.createLogger({
  level: "info",
  format: winston.format.combine(
    winston.format.colorize(),
    winston.format.timestamp({
      format: "YYYY-MM-DD HH:mm:ss",
    }),
    winston.format.printf(({ timestamp, level, message, stack }) => {
      if (stack) {
        return `${timestamp} [${level}]: ${message}\n${stack}`;
      }
      return `${timestamp} [${level}]: ${message}`;
    }),
  ),
  transports: [new winston.transports.Console()],
});

export const logger = {
  debug: (message: string): void => {
    winstonLogger.debug(message);
  },
  info: (message: string): void => {
    winstonLogger.info(message);
  },
  warn: (message: string): void => {
    winstonLogger.warn(message);
  },
  error: (message: string): void => {
    winstonLogger.error(message);
  },
};
