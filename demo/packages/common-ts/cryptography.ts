import * as ed from "@noble/ed25519";
import { encodeBase58, decodeBase58 } from "@std/encoding/base58";
import {
  type Result,
  createSuccess,
  createFailure,
  catchErrSync,
} from "./types.ts";
import { sha512 } from "@noble/hashes/sha512";

ed.etc.sha512Sync = (...m) => sha512(ed.etc.concatBytes(...m));

export type Ed25519Keypair = {
  privateKey: Uint8Array;
  publicKey: Uint8Array;
};

export function deserializeEd25519Keypair(
  base58PrivateKey: string
): Result<Ed25519Keypair> {
  // Decode the base58 string to bytes
  const keypairBytes = catchErrSync(() => decodeBase58(base58PrivateKey));

  if (!keypairBytes.success) {
    return createFailure(keypairBytes.error);
  }

  // First 32 bytes are the seed and private key
  const privateKey = keypairBytes.data.slice(0, 32);

  // With @noble/ed25519, you can get the public key from private
  const publicKey = catchErrSync(() => ed.getPublicKey(privateKey));

  if (!publicKey.success) {
    return createFailure(publicKey.error);
  }

  return createSuccess({
    privateKey,
    publicKey: publicKey.data,
  });
}

export function serializeEd25519Keypair(
  keypair: Ed25519Keypair
): Result<string> {
  // Combine private and public key bytes
  const keypairBytes = new Uint8Array(64);
  keypairBytes.set(keypair.privateKey, 0);
  keypairBytes.set(keypair.publicKey, 32);

  // Encode the combined bytes to base58
  return catchErrSync(() => encodeBase58(keypairBytes));
}

export function signEd25519(
  keypair: Ed25519Keypair,
  message: Uint8Array
): Result<Uint8Array> {
  return catchErrSync(() => ed.sign(message, keypair.privateKey));
}

export function verifyEd25519(
  keypair: Ed25519Keypair,
  message: Uint8Array,
  signature: Uint8Array
): Result<boolean> {
  return catchErrSync(() => ed.verify(signature, message, keypair.publicKey));
}

export function calculateSolanaAddress(publicKey: Uint8Array): Result<string> {
  return catchErrSync(() => encodeBase58(publicKey));
}

/**
 * Generates a deterministic pseudorandom number between 0 and n-1
 *
 * @param {Uint8Array} seed - The seed value
 * @param {number} roundId - Numeric identifier for this round slash draw
 * @param {number} n - Upper bound for the random number (exclusive)
 * @returns {number} - A number between 0 and n-1
 */
export async function deterministicRandom(
  seed: Uint8Array,
  roundId: number,
  n: number,
): Promise<number> {
  // Convert number to a byte array (8 bytes for a 64-bit number)
  const message: Uint8Array = new Uint8Array(8);
  new DataView(message.buffer).setBigUint64(0, BigInt(roundId), false);

  // Create HMAC using native Deno crypto
  let hmacData: Uint8Array = await createHmac(seed, message);

  // To avoid modulo bias, we use rejection sampling
  // We find the largest multiple of n that fits within UINT32_MAX
  const UINT32_MAX: number = 2 ** 32 - 1;
  const remainder: number = UINT32_MAX % n;
  const limit: number = UINT32_MAX - remainder;

  // Keep generating numbers until we get one within our desired range
  let randomValue: number;
  let i: number = 0;

  do {
    if (i > 0) {
      const newMessage: Uint8Array = new Uint8Array(8);
      new DataView(newMessage.buffer).setBigUint64(
        0,
        BigInt(roundId + i),
        false,
      );
      hmacData = await createHmac(seed, newMessage);
    }

    randomValue = new DataView(hmacData.buffer).getUint32(0, false);
    i++;
  } while (randomValue > limit);

  // Now we can safely use modulo without bias
  return randomValue % n;
}

/**
 * Creates an HMAC using Deno's standard library
 *
 * @param {Uint8Array} key - The key for HMAC
 * @param {Uint8Array} message - The message to hash
 * @returns {Uint8Array} - The HMAC result
 */
async function createHmac(
  key: Uint8Array,
  message: Uint8Array,
): Promise<Uint8Array> {
  return new Uint8Array(
    await crypto.subtle.digest("SHA-256", concatUint8Arrays(key, message)),
  );
}

/**
 * Helper function to concatenate Uint8Arrays
 */
function concatUint8Arrays(a: Uint8Array, b: Uint8Array): Uint8Array {
  const result = new Uint8Array(a.length + b.length);
  result.set(a, 0);
  result.set(b, a.length);
  return result;
}