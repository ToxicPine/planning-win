/**
 * Node status service for tracking the status of compute nodes
 */
import {
  NodeStatusData,
  HeartbeatData,
  OracleStats,
  NodeStatus,
} from "@scope/common-ts/schemas";
import { Logger } from "@scope/common-ts/types";

/**
 * Service for tracking and managing node status information
 */
export class NodeStatusService {
  private nodeStatusMap = new Map<string, NodeStatusData>();
  private totalHeartbeats = 0;
  private startTime = Math.floor(Date.now() / 1000);
  private offlineThresholdMs: number;
  private logger: Logger;

  constructor(logger: Logger, offlineThresholdMs: number) {
    this.logger = logger;
    this.offlineThresholdMs = offlineThresholdMs;
  }

  /**
   * Records a heartbeat from a node
   *
   * @param publicKey The node's public key
   * @param heartbeatData The heartbeat data from the node
   * @returns true if this is a new node, false if it's an existing node
   */
  recordHeartbeat(publicKey: string, heartbeatData: HeartbeatData): boolean {
    const existingStatus = this.nodeStatusMap.get(publicKey);
    const nodeStatus: NodeStatusData = {
      nodeAddress: publicKey,
      lastHeartbeat: heartbeatData.timestamp,
      status: heartbeatData.nodeStatus,
      hasCapacity: heartbeatData.hasCapacity,
    };

    this.nodeStatusMap.set(publicKey, nodeStatus);
    this.totalHeartbeats++;

    return !existingStatus;
  }

  /**
   * Gets the current system statistics
   */
  getSystemStats(): OracleStats {
    return {
      totalNodes: this.nodeStatusMap.size,
      onlineNodes: this.countNodesByStatus("online"),
      availableNodes: this.countNodesWithCapacity(),
      offlineNodes: this.countNodesByStatus("offline"),
      totalHeartbeats: this.totalHeartbeats,
      startTime: this.startTime,
    };
  }

  /**
   * Gets all node status information
   */
  getAllNodeStatus(): NodeStatusData[] {
    return Array.from(this.nodeStatusMap.values());
  }

  /**
   * Cleans up nodes that haven't sent heartbeats recently
   *
   * @returns Number of nodes marked as offline
   */
  cleanupOfflineNodes(): number {
    const now = Date.now();
    let offlineCount = 0;

    this.nodeStatusMap.forEach((node, publicKey) => {
      const lastHeartbeatTime = node.lastHeartbeat
        ? node.lastHeartbeat * 1000
        : 0;

      // Mark as offline if no heartbeat in configured threshold
      if (
        now - lastHeartbeatTime > this.offlineThresholdMs &&
        node.status !== "offline"
      ) {
        this.nodeStatusMap.set(publicKey, {
          ...node,
          status: "offline",
        });
        offlineCount++;
      }
    });

    if (offlineCount > 0) {
      this.logger.info({ offlineCount }, "Marked Inactive Nodes As Offline");
    }

    return offlineCount;
  }

  /**
   * Counts the number of nodes with a specific status
   */
  private countNodesByStatus(status: NodeStatus): number {
    let count = 0;
    const now = Date.now();

    this.nodeStatusMap.forEach((node) => {
      // Mark nodes as offline if they haven't sent a heartbeat recently
      if (status === "offline") {
        const lastHeartbeatTime = node.lastHeartbeat
          ? node.lastHeartbeat * 1000
          : 0;
        if (now - lastHeartbeatTime > this.offlineThresholdMs) {
          count++;
        }
      } else if (node.status === status) {
        // Check if it's actually online based on heartbeat time
        if (status === "online") {
          const lastHeartbeatTime = node.lastHeartbeat
            ? node.lastHeartbeat * 1000
            : 0;
          if (now - lastHeartbeatTime <= this.offlineThresholdMs) {
            count++;
          }
        } else {
          count++;
        }
      }
    });

    return count;
  }

  /**
   * Counts the number of nodes with available capacity
   */
  private countNodesWithCapacity(): number {
    let count = 0;
    const now = Date.now();

    this.nodeStatusMap.forEach((node) => {
      const lastHeartbeatTime = node.lastHeartbeat
        ? node.lastHeartbeat * 1000
        : 0;
      if (
        node.status === "online" &&
        node.hasCapacity &&
        now - lastHeartbeatTime <= this.offlineThresholdMs
      ) {
        count++;
      }
    });

    return count;
  }
}
