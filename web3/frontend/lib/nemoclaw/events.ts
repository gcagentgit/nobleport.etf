/**
 * Nemoclaw v1 — Eventing & Idempotency
 *
 * Implements event metadata requirements (§9.1), idempotency rules (§9.2),
 * and replay protection (§9.3).
 */

import { randomUUID } from 'crypto';
import { ActionClass, NemoclawEvent } from './types';

// ─── Idempotency Enforcer (§9.2) ─────────────────────────────────

export class IdempotencyEnforcer {
  private processedKeys = new Map<string, number>(); // key -> timestamp
  private dedupeWindowMs: number;

  constructor(dedupeWindowMs: number = 3_600_000) {
    this.dedupeWindowMs = dedupeWindowMs;
  }

  /** Check if an event has already been processed within the dedupe window */
  isProcessed(idempotencyKey: string, now: number): boolean {
    const lastProcessed = this.processedKeys.get(idempotencyKey);
    if (lastProcessed !== undefined && now - lastProcessed < this.dedupeWindowMs) {
      return true;
    }
    return false;
  }

  /** Mark an event as processed */
  markProcessed(idempotencyKey: string, now: number): void {
    this.processedKeys.set(idempotencyKey, now);
  }

  /** Prune stale entries */
  prune(now: number): number {
    let pruned = 0;
    for (const [key, ts] of this.processedKeys) {
      if (now - ts >= this.dedupeWindowMs) {
        this.processedKeys.delete(key);
        pruned++;
      }
    }
    return pruned;
  }
}

// ─── Replay Protection (§9.3) ────────────────────────────────────

export class ReplayProtector {
  private executedPayloadHashes = new Map<string, {
    proposalId: string;
    executedAt: number;
  }>();

  /** Record a payload hash as executed */
  recordExecution(payloadHash: string, proposalId: string): void {
    this.executedPayloadHashes.set(payloadHash, {
      proposalId,
      executedAt: Date.now(),
    });
  }

  /**
   * Check if a payload hash can be executed.
   * §9.3: Previously executed payload may not be re-executed unless:
   * - new proposal ID is created
   * - explicit re-approval occurs
   * - replay flag is set and logged
   */
  canExecute(
    payloadHash: string,
    proposalId: string,
    replayFlagSet: boolean,
  ): { allowed: boolean; reason: string } {
    const existing = this.executedPayloadHashes.get(payloadHash);
    if (!existing) {
      return { allowed: true, reason: 'First execution of this payload hash' };
    }

    // New proposal ID → allowed
    if (existing.proposalId !== proposalId) {
      return { allowed: true, reason: 'New proposal ID for previously executed payload' };
    }

    // Replay flag set → allowed (with logging)
    if (replayFlagSet) {
      return { allowed: true, reason: 'Replay flag explicitly set and logged' };
    }

    return {
      allowed: false,
      reason: `Payload hash ${payloadHash} already executed by proposal ${existing.proposalId} at ${existing.executedAt}`,
    };
  }
}

// ─── Event Builder (§9.1) ────────────────────────────────────────

export function createEvent(params: {
  correlationId: string;
  parentEventId?: string;
  producer: string;
  actionClass: ActionClass;
  targetEntityId: string;
  payload: unknown;
}): NemoclawEvent {
  return {
    eventId: randomUUID(),
    correlationId: params.correlationId,
    parentEventId: params.parentEventId,
    idempotencyKey: `${params.correlationId}:${params.targetEntityId}:${Date.now()}`,
    timestamp: Date.now(),
    producer: params.producer,
    actionClass: params.actionClass,
    targetEntityId: params.targetEntityId,
    payload: params.payload,
  };
}

// ─── Event Processor ─────────────────────────────────────────────

export class EventProcessor {
  private idempotencyEnforcer: IdempotencyEnforcer;
  private replayProtector: ReplayProtector;
  private eventLog: NemoclawEvent[] = [];

  constructor(dedupeWindowMs?: number) {
    this.idempotencyEnforcer = new IdempotencyEnforcer(dedupeWindowMs);
    this.replayProtector = new ReplayProtector();
  }

  /**
   * Process an execution-bound event with idempotency enforcement.
   * Returns whether the event was processed (false if duplicate).
   */
  processEvent(event: NemoclawEvent): {
    processed: boolean;
    reason: string;
  } {
    const now = Date.now();

    // §9.2: idempotency check
    if (this.idempotencyEnforcer.isProcessed(event.idempotencyKey, now)) {
      return {
        processed: false,
        reason: `Duplicate event: idempotency key ${event.idempotencyKey} already processed`,
      };
    }

    // Record and log
    this.idempotencyEnforcer.markProcessed(event.idempotencyKey, now);
    this.eventLog.push(event);

    return { processed: true, reason: 'Event processed successfully' };
  }

  /** Get replay protector for payload hash checks */
  getReplayProtector(): ReplayProtector {
    return this.replayProtector;
  }

  /** Get event log */
  getEventLog(): readonly NemoclawEvent[] {
    return this.eventLog;
  }

  /** Prune stale idempotency entries */
  prune(now: number): number {
    return this.idempotencyEnforcer.prune(now);
  }
}
