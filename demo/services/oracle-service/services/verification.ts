/**
 * Verification service for handling heartbeat signature verification
 */
import * as ed from "@noble/ed25519";
import { decodeBase58 } from "@std/encoding/base58";

import { HeartbeatData } from "@scope/common-ts/schemas";
import { Result, Logger } from "@scope/common-ts/types";

/**
 * Service to handle cryptographic verification of heartbeat data
 */
export class VerificationService {
  private logger: Logger;

  constructor(logger: Logger) {
    this.logger = logger;
  }

  /**
   * Verifies the signature of heartbeat data
   *
   * @param payload The heartbeat data payload
   * @param signature Base58-encoded signature
   * @param publicKey Base58-encoded public key
   * @returns Result indicating success or failure with verification result
   */
  async verifyHeartbeatSignature(
    givenPayload: HeartbeatData,
    givenSignature: string,
    givenPublicKey: string,
  ): Promise<Result<boolean>> {
    try {
      // Convert the data and signatures to the format needed for verification
      const signatureBytes = decodeBase58(givenSignature);
      const publicKeyBytes = decodeBase58(givenPublicKey);
      const dataString = JSON.stringify(givenPayload);
      const dataBytes = new TextEncoder().encode(dataString);

      // Verify the signature using noble ed25519
      const isValid = await ed.verify(signatureBytes, dataBytes, publicKeyBytes);

      // Log the verification result with truncated public key for privacy
      this.logger.debug(
        {
          publicKey: givenPublicKey.substring(0, 10) + "...",
          isValid,
        },
        "Signature Verification Completed",
      );

      return {
        success: true,
        data: isValid,
      };
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      this.logger.error(
        {
          publicKey: givenPublicKey.substring(0, 10) + "...",
          error: errorMessage,
        },
        "Signature Verification Error",
      );

      return {
        success: false,
        error: `Signature verification error: ${errorMessage}`,
        errorCode: "SIGNATURE_VERIFICATION_ERROR",
      };
    }
  }

  /**
   * Verifies that a timestamp is recent (within maxAge seconds)
   *
   * @param timestamp Timestamp to verify (in seconds since epoch)
   * @param maxAgeSeconds Maximum age in seconds
   * @returns true if timestamp is recent, false otherwise
   */
  isTimestampRecent(timestamp: number, maxAgeSeconds: number = 60): boolean {
    const currentTime = Math.floor(Date.now() / 1000);
    const timeDiff = Math.abs(currentTime - timestamp);

    return timeDiff <= maxAgeSeconds;
  }
}
