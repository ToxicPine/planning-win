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
  base58PrivateKey: string,
): Result<Ed25519Keypair> {
  // Decode the base58 string to bytes
  const keypairBytes = catchErrSync(() => decodeBase58(base58PrivateKey));

  if (!keypairBytes.success) {
    return createFailure(keypairBytes.error);
  }

  // First 32 bytes are the seed/private key
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
  keypair: Ed25519Keypair,
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
  message: Uint8Array,
): Result<Uint8Array> {
  return catchErrSync(() => ed.sign(message, keypair.privateKey));
}

export function verifyEd25519(
  keypair: Ed25519Keypair,
  message: Uint8Array,
  signature: Uint8Array,
): Result<boolean> {
  return catchErrSync(() => ed.verify(signature, message, keypair.publicKey));
}

export function calculateSolanaAddress(publicKey: Uint8Array): Result<string> {
  return catchErrSync(() => encodeBase58(publicKey));
}
