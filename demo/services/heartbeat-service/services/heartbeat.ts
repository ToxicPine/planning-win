/**
 * Heartbeat service responsible for sending heartbeats to oracle nodes
 */
import * as ed from "@noble/ed25519";
import { encodeBase58, decodeBase58 } from "@std/encoding/base58";

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
  private oracleUrls: string[];
  private nodeStatus: ComputeStatus = {
    status: "idle",
    hasCapacity: true,
    lastUpdated: Math.floor(Date.now() / 1000),
  };

  constructor(logger: Logger, oracleUrls: string[]) {
    this.logger = logger;
    this.oracleUrls = oracleUrls;
  }

  /**
   * Updates the node status based on compute service updates
   */
  updateNodeStatus(status: ComputeStatus): void {
    this.nodeStatus = {
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

      this.logger.debug({ heartbeatData }, "Generating heartbeat");

      // Sign the heartbeat data
      const signedData = await this.signHeartbeatData(heartbeatData);

      // Send to all Oracle Committee nodes
      this.logger.debug(
        { oracleCount: this.oracleUrls.length },
        "Sending heartbeats to oracle nodes",
      );

      // Send to all oracles concurrently
      const results = await Promise.allSettled(
        this.oracleUrls.map((oracleUrl) =>
          this.sendHeartbeatToOracle(oracleUrl, signedData),
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
          "Heartbeat round completed",
        );
      } else if (failCount > 0) {
        this.logger.warning(
          { failCount, total: results.length },
          "All heartbeats failed in this round",
        );
      }

      return { successCount, failCount };
    } catch (error) {
      this.logger.error({ error }, "Critical error in heartbeat process");
      return { successCount: 0, failCount: this.oracleUrls.length };
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
    oracleUrl: string,
    signedData: SignedHeartbeatData,
  ): Promise<HeartbeatResult> {
    try {
      const response = await fetch(`${oracleUrl}/api/heartbeat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(signedData),
      });

      if (!response.ok) {
        const errorText = await response.text();
        this.logger.warning(
          {
            oracleUrl,
            status: response.status,
            error: errorText,
          },
          "Heartbeat Request Failed",
        );
        return { success: false, oracleUrl, status: response.status };
      }

      const heartbeatResponse: HeartbeatResponse = await response.json();
      this.logger.info(
        {
          oracleUrl,
          success: heartbeatResponse.success,
          message: heartbeatResponse.message,
          status: heartbeatResponse.status,
        },
        "Heartbeat Sent Successfully",
      );

      return {
        success: true,
        oracleUrl,
        response: heartbeatResponse,
      };
    } catch (error) {
      this.logger.error({ oracleUrl, error }, "Error Sending Heartbeat");
      return {
        success: false,
        oracleUrl,
        error,
      };
    }
  }
}
