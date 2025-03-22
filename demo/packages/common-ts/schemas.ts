/**
 * Schema definitions for validating data structures
 */
import {
  object,
  string,
  boolean,
  number,
  picklist,
  array,
  regex,
  optional,
  nullable,
  pipe,
  url,
} from "@valibot/valibot";
import type { InferOutput } from "@valibot/valibot";

// Enums and constants

/** Possible node status values */
export const NODE_STATUS = ["online", "offline", "unknown"] as const;
export type NodeStatus = (typeof NODE_STATUS)[number];

/** Log level values */
export const LOG_LEVELS = [
  "NOTSET",
  "DEBUG",
  "INFO",
  "WARNING",
  "ERROR",
  "CRITICAL",
] as const;
export type LogLevel = (typeof LOG_LEVELS)[number];

// Base schemas

/** Node's unique Solana address */
export const NodeAddress = string();

/** Unix timestamp in seconds */
export const Timestamp = number();

/** Status with allowed values */
export const NodeStatus = picklist(NODE_STATUS);

// Log configuration

/** Configuration for logging */
export const LogConfigSchema = object({
  level: picklist(LOG_LEVELS, "INFO"),
  format: optional(boolean(), false), // Default to false (plain text)
  context: optional(object({}), {}),
});

// Core data schemas

/** Core heartbeat data payload */
export const HeartbeatDataSchema = object({
  timestamp: Timestamp,
  nodeStatus: NodeStatus,
  hasCapacity: optional(boolean(), false),
});

/** Cryptographically signed heartbeat data */
export const SignedHeartbeatDataSchema = object({
  payload: HeartbeatDataSchema,
  signature: string(),
  publicKey: string(),
});

/** Response to a heartbeat submission */
export const HeartbeatResponseSchema = object({
  success: optional(boolean(), false),
  message: string(),
  timestamp: Timestamp,
  status: NodeStatus,
});

/** Node status information */
export const NodeStatusDataSchema = object({
  nodeAddress: string(),
  lastHeartbeat: nullable(number()),
  status: NodeStatus,
  hasCapacity: optional(boolean(), false),
});

/** Oracle Committee statistics */
export const OracleStatsSchema = object({
  totalNodes: number(),
  onlineNodes: number(),
  availableNodes: number(),
  offlineNodes: number(),
  totalHeartbeats: number(),
  startTime: Timestamp,
});

// Configuration schemas

/** Heartbeat client configuration */
export const HeartbeatClientConfigSchema = object({
  port: number(),
  hostname: pipe(string(), url()),
  oracleUrls: array(pipe(string(), url())),
  nodePrivateKeyBase58: pipe(string(), regex(/^[1-9A-HJ-NP-Za-km-z]+$/)),
  heartbeatIntervalMs: number(),
  log: LogConfigSchema,
});

/** Oracle server configuration */
export const OracleServerConfigSchema = object({
  port: number(),
  otherOracleUrls: array(pipe(string(), url())),
  nodePrivateKeyBase58: pipe(string(), regex(/^[1-9A-HJ-NP-Za-km-z]+$/)),
  offlineThresholdMs: number(),
  cleanupIntervalMs: number(),
  log: LogConfigSchema,
});

// Export type definitions derived from schemas
export type HeartbeatData = InferOutput<typeof HeartbeatDataSchema>;
export type SignedHeartbeatData = InferOutput<typeof SignedHeartbeatDataSchema>;
export type HeartbeatResponse = InferOutput<typeof HeartbeatResponseSchema>;
export type NodeStatusData = InferOutput<typeof NodeStatusDataSchema>;
export type OracleStats = InferOutput<typeof OracleStatsSchema>;
export type LogConfig = InferOutput<typeof LogConfigSchema>;
export type HeartbeatClientConfig = InferOutput<
  typeof HeartbeatClientConfigSchema
>;
export type OracleServerConfig = InferOutput<typeof OracleServerConfigSchema>;
