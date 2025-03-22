import { Hono } from "hono";
import {
  HeartbeatClientConfig,
  HeartbeatClientConfigSchema,
} from "@scope/common-ts/schemas";

import {
  StatusUpdateResponse,
  HealthCheckResponse,
  ComputeStatus,
  Logger,
} from "@scope/common-ts/types";

import { createLogger } from "@scope/common-ts/logger";
import { loadConfig } from "@scope/common-ts/config";
import { HeartbeatService } from "./services/heartbeat.ts";

// Application version and constants
const APP_VERSION = "1.0.0";
const APP_NAME = "heartbeat-client";

// Load configuration from environment
const ENV_PREFIX = "HEARTBEAT_CLIENT_";
const DEFAULT_CONFIG = {
  port: 8000,
  oracleUrls: ["http://localhost:8001"],
  heartbeatIntervalMs: 30 * 1000,
  log: { level: "INFO", format: false },
};

const configResult = loadConfig(HeartbeatClientConfigSchema, ENV_PREFIX);

// Get the config, using defaults if invalid
const config: HeartbeatClientConfig = configResult.success
  ? configResult.data
  : (DEFAULT_CONFIG as HeartbeatClientConfig);

// Initialize logger with application context
const logger: Logger = createLogger({
  level: config.log.level,
  format: config.log.format,
  context: {
    app: APP_NAME,
    version: APP_VERSION,
  },
});

// Log startup information
if (!configResult.success) {
  logger.warning(
    {
      error: configResult.error,
      errorCode: configResult.errorCode,
    },
    "Configuration Validation Failed, Using Defaults",
  );
}

// Initialize the heartbeat service
const heartbeatService = new HeartbeatService(logger, config.oracleUrls);

// Initialize the API server
const app = new Hono();

// Basic welcome route
app.get("/", (c) => {
  return c.text("SplitUp Node Heartbeat Service");
});

// Add a compute status endpoint for intra-node communication
app.post("/api/compute-status", async (c) => {
  try {
    const body = (await c.req.json()) as ComputeStatus;

    // Update the heartbeat service with compute status
    heartbeatService.updateNodeStatus(body);

    logger.debug(
      { hasCapacity: body.hasCapacity, status: body.status },
      "Received Compute Status Update",
    );

    const response: StatusUpdateResponse = {
      success: true,
      message: "Status Updated Successfully",
    };

    return c.json(response);
  } catch (error) {
    logger.error({ error }, "Error Processing Compute Status Update");
    const response: StatusUpdateResponse = {
      success: false,
      message: "Failed To Process Status Update",
    };
    return c.json(response, 500);
  }
});

// Health check endpoint
app.get("/health", (c) => {
  const response: HealthCheckResponse = {
    status: "healthy",
    version: APP_VERSION,
    uptime: Math.floor(Date.now() / 1000 - startTime),
  };

  return c.json(response);
});

// Track server start time
const startTime = Math.floor(Date.now() / 1000);

// Initialize the system
async function initialize(): Promise<void> {
  try {
    logger.info(
      {
        port: config.port,
        heartbeatInterval: config.heartbeatIntervalMs,
        oracleCount: config.oracleUrls.length,
      },
      "Starting SplitUp Node Heartbeat Service",
    );

    // Initialize the keypair
    await heartbeatService.initializeKeyPair(config.nodePrivateKeyBase58);

    // Set up heartbeat interval
    const intervalMs = config.heartbeatIntervalMs;
    setInterval(() => heartbeatService.sendHeartbeats(), intervalMs);

    // Send initial heartbeat
    heartbeatService.sendHeartbeats().catch((error: unknown) => {
      logger.error({ error }, "Initial Heartbeat Failed");
    });

    // Start the server
    Deno.serve({ port: config.port }, app.fetch);
  } catch (error) {
    logger.critical({ error }, "Failed To Initialize Heartbeat Service");
    Deno.exit(1);
  }
}

// Start the application
initialize();
