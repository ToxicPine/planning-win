import type { LivenessTable, OracleSignedNodeSelection } from "../types.ts";
import type { NodeStatusData } from "@scope/common-ts/schemas";
import {
  deserializeEd25519Keypair,
  Ed25519Keypair,
  signEd25519,
  deterministicRandom,
} from "@scope/common-ts/cryptography";

/**
 * Service for consensus rounds
 */
export class ConsensusService {
  private oracleCommittee: {
    oracleId: string;
    url: string;
  }[];
  private keypair: Ed25519Keypair;

  constructor(
    oracleCommittee: {
      oracleId: string;
      url: string;
    }[],
    publicKey: string
  ) {
    this.oracleCommittee = oracleCommittee;
    const result = deserializeEd25519Keypair(publicKey);
    if (!result.success) {
      throw new Error("Invalid public key");
    }
    this.keypair = result.data;
  }

  /**
   * Hash a liveness table
   * @param nodeStatusData - The node status data
   * @returns The hash of the liveness table
   */
  private async hashTable(nodeStatusData: NodeStatusData[]): Promise<string> {
    const tableString = nodeStatusData
      .map(
        (node) =>
          `${node.nodeAddress}:${node.status}:${node.lastHeartbeat}:${node.hasCapacity}`
      )
      .join("|");

    const encoder = new TextEncoder();
    const data = encoder.encode(tableString);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    return hashHex;
  }

  /**
   * Generate a liveness table from the node status data
   * @param roundId - The round id
   * @param nodeStatusData - The node status data
   * @returns The liveness table that is filtered to only include the nodes that are relevant to the task
   */
  private async generateLivenessTable(
    roundId: number,
    nodeStatusData: NodeStatusData[]
  ): Promise<LivenessTable> {
    const sortedData = nodeStatusData.sort((a, b) => {
      if (a.status === b.status) {
        return a.nodeAddress.localeCompare(b.nodeAddress);
      }
      // Fix the status comparison
      return a.status.localeCompare(b.status);
    });

    const tableHash = await this.hashTable(sortedData);

    return {
      roundId: roundId,
      updates: sortedData,
      tableHash,
      timestamp: Date.now(),
    };
  }

  /**
   * Start a consensus round
   * @param taskId - The task id
   * @param roundId - The round id
   * @param nodeStatusData - The node status data
   * @returns The signed node selection
   */
  public async startConsensusRound(
    taskId: string,
    roundId: number,
    nodeStatusData: NodeStatusData[]
  ): Promise<OracleSignedNodeSelection> {
    const livenessTable = await this.generateLivenessTable(
      roundId,
      nodeStatusData
    );

    const majorityTable = await this.contactOracleCommittee(livenessTable);

    const randomIndex = await deterministicRandom(
      new TextEncoder().encode(majorityTable.tableHash),
      roundId,
      majorityTable.updates.length + 1
    );

    const selection = majorityTable.updates[randomIndex];

    const message = new TextEncoder().encode(selection.nodeAddress);
    const signatureResult = signEd25519(this.keypair, message);

    if (!signatureResult.success) {
      throw new Error("Failed to sign message");
    }

    return {
      selection: {
        taskId,
        selectedNode: selection.nodeAddress,
        vrfSeed: majorityTable.tableHash,
        roundId,
        timestamp: Date.now(),
      },
      signature: signatureResult.data.toString(),
    };
  }

  /**
   * Contact the oracle committee and get the majority table
   * @param livenessTable - The liveness table
   * @returns The majority table
   */
  private async contactOracleCommittee(
    livenessTable: LivenessTable
  ): Promise<LivenessTable> {
    const responses = await Promise.all(
      this.oracleCommittee.map((oracle) => fetch(oracle.url + "/api/liveness"))
    );

    const results: LivenessTable[] = await Promise.all(
      responses
        .filter((response) => response.ok)
        .map((response) => response.json())
    );

    const tables = [...results, livenessTable];

    const tableHashes = tables.map((table) => table.tableHash);

    // Count occurrences of each hash
    const hashCounts = new Map<string, number>();
    tableHashes.forEach((hash) => {
      hashCounts.set(hash, (hashCounts.get(hash) || 0) + 1);
    });

    // Find the most common hash
    let majorityHash = "";
    let maxCount = 0;
    hashCounts.forEach((count, hash) => {
      if (count > maxCount) {
        maxCount = count;
        majorityHash = hash;
      }
    });

    const majorityTable =
      results.find((table) => table.tableHash === majorityHash) ??
      livenessTable;

    return majorityTable;
  }
}
