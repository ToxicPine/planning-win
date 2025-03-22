import { Hono } from "hono";

import {
  StatusUpdateResponse,
  HealthCheckResponse,
  ComputeStatus,
} from "@scope/common-ts/types";

import { config, logger, APP_VERSION } from "./config.ts";
import { HeartbeatService } from "./services/heartbeat.ts";

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
