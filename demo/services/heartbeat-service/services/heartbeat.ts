/**
 * Heartbeat service responsible for sending heartbeats to oracle nodes
 */
import * as ed from "@noble/ed25519";
import { hc } from "hono/client";
import { encodeBase58, decodeBase58 } from "@std/encoding/base58";
import type { AppType } from "@scope/oracle-service/types";

import {
  HeartbeatData,
  SignedHeartbeatData,
  HeartbeatResponse,
} from "@scope/common-ts/schemas";

import {
  PromiseSettledResult,
  ComputeStatus,
  Logger,
} from "@scope/common-ts/types";

/**
 * Result of sending a heartbeat to an oracle
 */
export interface HeartbeatResult {
  /** Whether the operation was successful */
  success: boolean;
  /** The URL of the oracle that was contacted */
  oracleUrl: string;
  /** HTTP status code if the request was made but failed */
  status?: number;
  /** Response from the oracle if successful */
  response?: HeartbeatResponse;
  /** Error details if the operation failed */
  error?: unknown;
}

/**
 * Ed25519 Keypair structure
 */
interface Ed25519KeyPair {
  publicKey: Uint8Array;
  privateKey: Uint8Array;
}

/**
 * Heartbeat service for sending node heartbeats to oracle nodes
 */
export class HeartbeatService {
  private nodeKeyPair: Ed25519KeyPair | null = null;
  private logger: Logger;
  private oracleClients: {
    url: string;
    clientObject: ReturnType<typeof hc<AppType>>;
  }[];
  private _nodeStatus: ComputeStatus = {
    status: "offline",
    hasCapacity: true,
    lastUpdated: Math.floor(Date.now() / 1000),
  };

  /**
   * Get the current node status
   */
  public get nodeStatus(): ComputeStatus {
    return this._nodeStatus;
  }

  constructor(logger: Logger, oracleUrls: string[]) {
    this.logger = logger;
    this.oracleClients = oracleUrls.map((url) => ({
      url,
      clientObject: hc<AppType>(url),
    }));
  }

  /**
   * Updates the node status based on compute service updates
   */
  updateNodeStatus(status: ComputeStatus): void {
    this._nodeStatus = {
      ...status,
      lastUpdated: Math.floor(Date.now() / 1000),
    };

    this.logger.debug(
      {
        hasCapacity: this.nodeStatus.hasCapacity,
        status: this.nodeStatus.status,
      },
      "Updated Node Status",
    );
  }

  /**
   * Initializes the keypair for the node
   */
  async initializeKeyPair(privateKeyBase58: string): Promise<void> {
    try {
      // Create keypair from private key
      this.nodeKeyPair =
        await this.getKeypairFromBase58String(privateKeyBase58);
      const publicKeyBase58 = encodeBase58(this.nodeKeyPair.publicKey);

      this.logger.info({ publicKey: publicKeyBase58 }, "Keypair Initialized");
    } catch (error) {
      this.logger.error({ error }, "Failed to Initialize Keypair");
      throw error;
    }
  }

  /**
   * Sends heartbeats to all configured oracle nodes
   */
  async sendHeartbeats(): Promise<{ successCount: number; failCount: number }> {
    try {
      // Generate heartbeat data
      const heartbeatData: HeartbeatData = {
        timestamp: Math.floor(Date.now() / 1000),
        nodeStatus: this.nodeStatus.status === "error" ? "offline" : "online",
        hasCapacity: this.nodeStatus.hasCapacity,
      };

      this.logger.debug({ heartbeatData }, "Generating Heartbeat");

      // Sign the heartbeat data
      const signedData = await this.signHeartbeatData(heartbeatData);

      // Send to all Oracle Committee nodes
      this.logger.debug(
        { oracleCount: this.oracleClients.length },
        "Sending Heartbeats to Oracle Nodes",
      );

      // Send to all oracles concurrently
      const results = await Promise.allSettled(
        this.oracleClients.map((client) =>
          this.sendHeartbeatToOracle(client, signedData),
        ),
      );

      // Count successes and failures
      const successCount = results.filter(
        (r: PromiseSettledResult<HeartbeatResult>) => {
          return r.status === "fulfilled" && r.value.success;
        },
      ).length;
      const failCount = results.length - successCount;

      if (successCount > 0) {
        this.logger.info(
          { successCount, failCount, total: results.length },
          "Heartbeat Round Completed",
        );
      } else if (failCount > 0) {
        this.logger.warning(
          { failCount, total: results.length },
          "All Heartbeats Failed in This Round",
        );
      }

      return { successCount, failCount };
    } catch (error) {
      this.logger.error({ error }, "Critical Error in Heartbeat Process");
      return { successCount: 0, failCount: this.oracleClients.length };
    }
  }

  /**
   * Converts a base58 private key string to a keypair
   */
  private async getKeypairFromBase58String(
    base58PrivateKey: string,
  ): Promise<Ed25519KeyPair> {
    if (!base58PrivateKey || base58PrivateKey.length === 0) {
      throw new Error("Invalid Private Key: Empty String Provided");
    }

    try {
      // Decode the base58 private key to bytes
      const privateKeyBytes = decodeBase58(base58PrivateKey);

      // Generate the public key from the private key
      const publicKeyBytes = await ed.getPublicKey(privateKeyBytes);

      return {
        publicKey: publicKeyBytes,
        privateKey: privateKeyBytes,
      };
    } catch (error) {
      this.logger.error(
        { error },
        "Failed to create keypair from private key string",
      );
      throw new Error("Invalid Private Key Format");
    }
  }

  /**
   * Signs heartbeat data with the node's keypair
   */
  private async signHeartbeatData(
    data: HeartbeatData,
  ): Promise<SignedHeartbeatData> {
    try {
      if (!this.nodeKeyPair) {
        throw new Error("Keypair Not Initialized");
      }

      // Convert the heartbeat data to bytes
      const dataString = JSON.stringify(data);
      const dataBytes = new TextEncoder().encode(dataString);

      // Sign the data
      const signature = await ed.sign(dataBytes, this.nodeKeyPair.privateKey);
      const signatureBase58 = encodeBase58(signature);
      const publicKeyBase58 = encodeBase58(this.nodeKeyPair.publicKey);

      this.logger.debug(
        {
          publicKey: publicKeyBase58,
          signaturePreview: signatureBase58.slice(0, 10) + "...", // Only log part of the signature for security
        },
        "Data Signed Successfully",
      );

      // Return the signed heartbeat data
      return {
        payload: data,
        signature: signatureBase58,
        publicKey: publicKeyBase58,
      };
    } catch (error) {
      this.logger.error({ error }, "Failed to Sign Heartbeat Data");
      throw error;
    }
  }

  /**
   * Sends a signed heartbeat to a single oracle node
   */
  private async sendHeartbeatToOracle(
    client: { url: string; clientObject: ReturnType<typeof hc<AppType>> },
    signedData: SignedHeartbeatData,
  ): Promise<HeartbeatResult> {
    try {
      // Use the Hono client instead of direct fetch
      const response = await client.clientObject.api.heartbeat.$post({
        json: signedData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        this.logger.warning(
          {
            oracleUrl: client.url,
            status: response.status,
            error: errorText,
          },
          "Heartbeat Request Failed",
        );
        return {
          success: false,
          oracleUrl: client.url,
          status: response.status,
        };
      }

      const heartbeatResponse = await response.json();
      this.logger.info(
        {
          oracleUrl: client.url,
          success: heartbeatResponse.success,
          message: heartbeatResponse.message,
          status: heartbeatResponse.status,
        },
        "Heartbeat Sent Successfully",
      );

      return {
        success: true,
        oracleUrl: client.url,
        response: heartbeatResponse,
      };
    } catch (error) {
      this.logger.error(
        { oracleUrl: client.url, error },
        "Error Sending Heartbeat",
      );
      return {
        success: false,
        oracleUrl: client.url,
        error,
      };
    }
  }
}
