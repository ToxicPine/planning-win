import { Logger } from "@scope/common-ts/types";
import {
  HeartbeatClientConfig,
  HeartbeatClientConfigSchema,
} from "@scope/common-ts/schemas";
import { createLogger } from "@scope/common-ts/logger";
import { loadConfig } from "@scope/common-ts/config";

// Application version and constants
export const APP_VERSION = "1.0.0";
export const APP_NAME = "heartbeat-client";

// Load configuration from environment
const ENV_PREFIX = "HEARTBEAT_CLIENT_";
export const configResult = loadConfig(HeartbeatClientConfigSchema, ENV_PREFIX);

// Create a temporary logger to log the error
let tempLogger: Logger | null = null;
tempLogger = createLogger({
  level: "WARNING",
  format: false,
  context: {
    app: APP_NAME,
    version: APP_VERSION,
  },
});

// Get the config, using defaults if invalid
if (!configResult.success) {
    tempLogger.warning(
        {
        error: configResult.error,
        errorCode: configResult.errorCode,
        },
        "Configuration Validation Failed",
    );
  Deno.exit(1);
}

// Make sure GC deallocates tempLogger
tempLogger = null;

export const config: HeartbeatClientConfig = configResult.data;

// Initialize logger with application context
export const logger: Logger = createLogger({
  level: config?.log.level ?? "INFO",
  format: config?.log.format ?? false,
  context: {
    app: APP_NAME,
    version: APP_VERSION,
  },
});