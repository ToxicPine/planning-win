/**
 * Centralized logging module for consistent logging across services
 */
import type { Logger, LoggerConfig } from "./types.ts";
import { LOG_LEVELS, type LogLevel } from "./schemas.ts";

/**
 * Create a new logger instance with the specified configuration
 *
 * @param config - Configuration for the logger
 * @returns A configured logger instance
 */
export function createLogger(config: LoggerConfig): Logger {
  // Default context to include in all logs
  const defaultContext = config.context || {};

  // Get the minimum log level index
  const minimumLevelIndex = LOG_LEVELS.indexOf(config.level);

  /**
   * Create a log handler function for a specific level
   */
  const createLogHandler = (level: LogLevel, levelIndex: number) => {
    // If the level is below the minimum level, return a no-op function
    if (levelIndex < minimumLevelIndex) {
      return () => {};
    }

    // Choose the appropriate console method based on level
    const consoleMethod = getConsoleMethod(level);

    // Return a function that logs with the specified level
    return (data: Record<string, unknown>, msg: string) => {
      const logData = {
        ...defaultContext,
        ...data,
        level,
        msg,
        timestamp: new Date().toISOString(),
      };

      // Output as JSON or formatted string based on config
      if (config.format) {
        consoleMethod(JSON.stringify(logData));
      } else {
        // Pretty format the message
        const prefix = `[${logData.timestamp}] ${level}:`;
        const details = Object.entries(data)
          .map(([key, value]) => `${key}=${formatValue(value)}`)
          .join(" ");

        consoleMethod(`${prefix} ${msg} ${details}`);
      }
    };
  };

  // Create the logger instance with handlers for each level
  return {
    debug: createLogHandler("DEBUG", 1),
    info: createLogHandler("INFO", 2),
    warning: createLogHandler("WARNING", 3),
    error: createLogHandler("ERROR", 4),
    critical: createLogHandler("CRITICAL", 5),
  };
}

/**
 * Get the appropriate console method for a log level
 */
function getConsoleMethod(level: LogLevel): (message: string) => void {
  switch (level) {
    case "DEBUG":
      return console.debug;
    case "INFO":
      return console.info;
    case "WARNING":
      return console.warn;
    case "ERROR":
    case "CRITICAL":
      return console.error;
    default:
      return console.log;
  }
}

/**
 * Format a value for pretty log output
 */
function formatValue(value: unknown): string {
  if (value === null) return "null";
  if (value === undefined) return "undefined";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean")
    return String(value);
  if (value instanceof Error) return value.message;
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return "[Object]";
    }
  }
  return String(value);
}

/**
 * Default logger configuration
 */
export const DEFAULT_LOGGER_CONFIG: LoggerConfig = {
  level: "INFO",
  format: false,
};

/**
 * Create a default console logger
 */
export function createDefaultLogger(overrides?: Partial<LoggerConfig>): Logger {
  return createLogger({
    ...DEFAULT_LOGGER_CONFIG,
    ...overrides,
  });
}
