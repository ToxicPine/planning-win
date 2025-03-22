import { safeParse } from "@valibot/valibot";
import type { BaseSchema, BaseIssue, InferOutput } from "@valibot/valibot";
import type { Result } from "./types.ts";

/**
 * Load environment variables with a specific prefix and convert them to appropriate types
 * @param envPrefix The prefix to filter environment variables by
 * @returns An object with the environment variables (without prefix)
 */
export function loadEnvVars(envPrefix: string = ""): Record<string, unknown> {
  const envVars: Record<string, unknown> = {};

  // Get all environment variables with the given prefix
  for (const [key, value] of Object.entries(Deno.env.toObject())) {
    if (key.startsWith(envPrefix)) {
      const configKey = key.replace(envPrefix, "").toLowerCase();

      // Handle boolean values
      if (value.toLowerCase() === "true") {
        envVars[configKey] = true;
      } else if (value.toLowerCase() === "false") {
        envVars[configKey] = false;
      }
      // Handle numeric values
      else if (!isNaN(Number(value))) {
        envVars[configKey] = Number(value);
      }
      // Handle array values (comma-separated strings)
      else if (value.includes(",")) {
        envVars[configKey] = value.split(",").map((item) => item.trim());
      }
      // Keep as string
      else {
        envVars[configKey] = value;
      }
    }
  }

  return envVars;
}

/**
 * Load configuration from environment variables with default values and validation.
 *
 * @param schema - Valibot schema for validation
 * @param prefix - Prefix for environment variables (e.g., 'APP_')
 * @param defaults - Default values to use when environment variables are not set
 * @returns - Result containing the validated configuration or error details
 */
export function loadConfig<
  T extends BaseSchema<unknown, unknown, BaseIssue<unknown>>,
>(schema: T, prefix: string = ""): Result<InferOutput<T>> {
  try {
    // Helper for converting string env var values to appropriate types
    const convertValue = (value: string): unknown => {
      if (value.toLowerCase() === "true") return true;
      if (value.toLowerCase() === "false") return false;
      if (value.toLowerCase() === "null") return null;
      if (value.toLowerCase() === "undefined") return undefined;
      if (/^-?\d+$/.test(value)) return parseInt(value, 10);
      if (/^-?\d+\.\d+$/.test(value)) return parseFloat(value);
      return value;
    };

    // Gather values from environment variables
    const envConfig: Record<string, unknown> = Object.entries(
      Deno.env.toObject(),
    )
      .filter(([key]) => key.startsWith(prefix))
      .reduce(
        (acc: Record<string, unknown>, [key, value]) => {
          acc[key] = convertValue(value);
          return acc;
        },
        {} satisfies Record<string, unknown>,
      );

    // Validate with schema
    const parseResult = safeParse(schema, envConfig);

    if (!parseResult.success) {
      const issues = parseResult.issues.map((issue) => ({
        path: issue.path?.map((p) => p.key).join("."),
        message: issue.message,
      }));

      return {
        success: false,
        error: `Configuration Validation Failed: ${issues.map((i) => `${i.path}: ${i.message}`).join(", ")}`,
        errorCode: "CONFIG_VALIDATION_ERROR",
        details: envConfig,
      };
    }

    return {
      success: true,
      data: parseResult.output,
    };
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      success: false,
      error: `Failed to load configuration: ${errorMessage}`,
      errorCode: "CONFIG_LOADING_ERROR",
    };
  }
}
