/**
 * Common type definitions used across the SplitUp application
 */

/**
 * Successful operation result
 */
export interface Success<T> {
  success: true;
  data: T;
}

/**
 * Failed operation result
 */
export interface Failure {
  success: false;
  error: string;
  errorCode?: string;
  details?: unknown;
}

/**
 * Result of any operation, either Success or Failure
 */
export type Result<T> = Success<T> | Failure;

/**
 * Standard health check response format for API endpoints
 */
export interface HealthCheckResponse {
  /** Current health status of the service */
  status: "healthy" | "degraded" | "unhealthy";

  /** Version of the application */
  version: string;

  /** Uptime in seconds */
  uptime: number;

  /** Additional health information (optional) */
  info?: Record<string, unknown>;
}

/**
 * Logger interface for consistent logging across applications
 */
export interface Logger {
  /** Log a debug message */
  debug: (data: Record<string, unknown>, msg: string) => void;

  /** Log an informational message */
  info: (data: Record<string, unknown>, msg: string) => void;

  /** Log a warning */
  warning: (data: Record<string, unknown>, msg: string) => void;

  /** Log an error */
  error: (data: Record<string, unknown>, msg: string) => void;

  /** Log a critical error */
  critical: (data: Record<string, unknown>, msg: string) => void;
}

export type LogLevel =
  | "NOTSET"
  | "DEBUG"
  | "INFO"
  | "WARNING"
  | "ERROR"
  | "CRITICAL";
export const LOG_LEVELS: LogLevel[] = [
  "NOTSET",
  "DEBUG",
  "INFO",
  "WARNING",
  "ERROR",
  "CRITICAL",
];

/**
 * Logger configuration options
 */
export interface LoggerConfig {
  /** Log level threshold */
  level: LogLevel;

  /** Whether to format logs as JSON (true) or plain text (false) */
  format: boolean;

  /** Context information to include with every log */
  context?: Record<string, unknown>;
}

/**
 * Promise.allSettled result types (re-export of standard types)
 */
export type PromiseSettledResult<T> =
  | PromiseFulfilledResult<T>
  | PromiseRejectedResult;

export interface PromiseFulfilledResult<T> {
  status: "fulfilled";
  value: T;
}

export interface PromiseRejectedResult {
  status: "rejected";
  reason: unknown;
}

/**
 * Status update from compute service to heartbeat service
 */
export interface ComputeStatus {
  status: "idle" | "busy" | "error";
  hasCapacity: boolean;
  lastUpdated: number; // timestamp
}

/**
 * Response to status update
 */
export interface StatusUpdateResponse {
  success: boolean;
  message: string;
}
