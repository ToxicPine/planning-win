import {
  SignedHeartbeatDataSchema,
  HeartbeatResponse,
  OracleServerConfig,
  OracleServerConfigSchema,
} from "@scope/common-ts/schemas";
import { loadConfig } from "@scope/common-ts/config";
import { createLogger } from "@scope/common-ts/logger";
import { VerificationService } from "./services/verification.ts";
import { NodeStatusService } from "./services/node-status.ts";
import { HealthCheckResponse, Logger } from "@scope/common-ts/types";
import { safeParse } from "@valibot/valibot";
import { Hono } from "hono";

// Application version and constants
const APP_VERSION = "1.0.0";
const APP_NAME = "oracle-server";

// Load configuration from environment
const ENV_PREFIX = "ORACLE_SERVER_";
const DEFAULT_CONFIG = {
  port: 8001,
  offlineThresholdMs: 90 * 1000,
  cleanupIntervalMs: 30 * 1000,
  log: {
    level: "INFO",
    format: false,
    context: {},
  },
};

const configResult = loadConfig(OracleServerConfigSchema, ENV_PREFIX);

// Get the config, using defaults if invalid
const config: OracleServerConfig = configResult.success
  ? configResult.data
  : (DEFAULT_CONFIG as OracleServerConfig);

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

// Initialize services
const verificationService = new VerificationService(logger);
const nodeStatusService = new NodeStatusService(
  logger,
  config.offlineThresholdMs,
);

// Initialize API server
const app = new Hono();

// Start time for uptime calculation
const startTime = Math.floor(Date.now() / 1000);

// Basic welcome route
app.get("/", (c) => {
  return c.text("SplitUp Oracle Committee Server");
});

// Stats endpoint to get system-wide statistics
app.get("/api/stats", (c) => {
  const stats = nodeStatusService.getSystemStats();
  logger.debug({ stats }, "Returning System Stats");
  return c.json(stats);
});

// Node status endpoint to get status of all nodes
app.get("/api/nodes", (c) => {
  const nodeStatusList = nodeStatusService.getAllNodeStatus();
  logger.debug(
    { nodeCount: nodeStatusList.length },
    "Returning node status list",
  );
  return c.json(nodeStatusList);
});

// Heartbeat endpoint to receive heartbeats from nodes
app.post("/api/heartbeat", async (c) => {
  try {
    // Parse the request body
    const body = await c.req.json();
    const validationResult = safeParse(SignedHeartbeatDataSchema, body);

    if (!validationResult.success) {
      logger.warning(
        { errors: validationResult.issues },
        "Invalid heartbeat data received",
      );
      return c.json(
        {
          success: false,
          message: "Invalid Heartbeat Data Format",
          timestamp: Math.floor(Date.now() / 1000),
          status: "unknown",
        } satisfies HeartbeatResponse,
        400,
      );
    }

    const signedHeartbeat = validationResult.output;
    const { payload, signature, publicKey } = signedHeartbeat;

    // Verify the timestamp is recent
    const currentTime = Math.floor(Date.now() / 1000);
    if (!verificationService.isTimestampRecent(payload.timestamp)) {
      logger.warning(
        {
          timestamp: payload.timestamp,
          currentTime,
          diff: Math.abs(currentTime - payload.timestamp),
          publicKey: publicKey.substring(0, 10) + "...",
        },
        "Heartbeat Timestamp Too Old or In The Future",
      );

      return c.json(
        {
          success: false,
          message: "Heartbeat Timestamp Too Old or In The Future",
          timestamp: currentTime,
          status: "unknown",
        } satisfies HeartbeatResponse,
        400,
      );
    }

    // Verify the signature
    const signatureResult = await verificationService.verifyHeartbeatSignature(
      payload,
      signature,
      publicKey,
    );

    if (!signatureResult.success) {
      logger.error(
        {
          error: signatureResult.error,
          publicKey: publicKey.substring(0, 10) + "...",
        },
        "Signature Verification Error",
      );

      return c.json(
        {
          success: false,
          message: "Signature Verification Error",
          timestamp: currentTime,
          status: "unknown",
        } satisfies HeartbeatResponse,
        500,
      );
    }

    if (!signatureResult.data) {
      logger.warning(
        {
          publicKey: publicKey.substring(0, 10) + "...",
        },
        "Invalid Signature For Heartbeat",
      );

      return c.json(
        {
          success: false,
          message: "Invalid Signature",
          timestamp: currentTime,
          status: "unknown",
        } satisfies HeartbeatResponse,
        401,
      );
    }

    // Record the heartbeat
    const isNewNode = nodeStatusService.recordHeartbeat(publicKey, payload);

    // Log the heartbeat
    if (isNewNode) {
      logger.info(
        {
          publicKey: publicKey.substring(0, 10) + "...", // Truncate for log readability
          status: payload.nodeStatus,
          hasCapacity: payload.hasCapacity,
          totalNodes: nodeStatusService.getSystemStats().totalNodes,
        },
        "Heartbeat Received From New Node",
      );
    } else {
      logger.info(
        {
          publicKey: publicKey.substring(0, 10) + "...", // Truncate for log readability
          status: payload.nodeStatus,
          hasCapacity: payload.hasCapacity,
          heartbeatCount: nodeStatusService.getSystemStats().totalHeartbeats,
        },
        "Heartbeat Received From Existing Node",
      );
    }

    // Return success response
    return c.json({
      success: true,
      message: "Heartbeat Received Successfully",
      timestamp: currentTime,
      status: payload.nodeStatus,
    } satisfies HeartbeatResponse);
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    logger.error({ error: errorMessage }, "Error Processing Heartbeat");

    return c.json(
      {
        success: false,
        message: "Error Processing Heartbeat",
        timestamp: Math.floor(Date.now() / 1000),
        status: "unknown",
      } satisfies HeartbeatResponse,
      500,
    );
  }
});

// Health check endpoint
app.get("/health", (c) => {
  const response: HealthCheckResponse = {
    status: "healthy",
    version: APP_VERSION,
    uptime: Math.floor(Date.now() / 1000) - startTime,
  };

  return c.json(response);
});

// Initialize the server
function initialize(): void {
  try {
    logger.info(
      {
        port: config.port,
        offlineThreshold: config.offlineThresholdMs / 1000 + "s",
        cleanupInterval: config.cleanupIntervalMs / 1000 + "s",
      },
      "Starting SplitUp Oracle Committee Server",
    );

    // Run Cleanup At The Specified Interval
    setInterval(
      () => nodeStatusService.cleanupOfflineNodes(),
      config.cleanupIntervalMs,
    );

    // Start the server
    Deno.serve({ port: config.port }, app.fetch);
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    logger.critical(
      { error: errorMessage },
      "Failed To Initialize Oracle Committee Server",
    );
    Deno.exit(1);
  }
}

// Start the application
initialize();
