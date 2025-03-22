import type { AppType as _AppType } from "./main.ts";
import type {
  Timestamp,
  NodeSelection,
  NodeStatusData,
} from "@scope/common-ts/schemas";

export type AppType = _AppType;

/** Oracle node identifier */
export type OracleId = string;

/** Consensus round identifier */
export type RoundId = number;

/** Hash of liveness table */
export type TableHash = string;

/** Complete node liveness table */
export interface LivenessTable {
  roundId: RoundId; // Current consensus round
  updates: NodeStatusData[]; // All node updates
  tableHash: TableHash; // Hash of the sorted table
  timestamp: Timestamp; // When table was created
}

/** Signed node selection from individual oracle **/
export interface OracleSignedNodeSelection {
  selection: NodeSelection;
  signature: string;
}
