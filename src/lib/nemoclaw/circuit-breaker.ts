/**
 * Nemoclaw v1 — Circuit Breakers & Kill Switches
 *
 * Implements automatic circuit breakers (§15.1), manual kill switches (§15.2),
 * and emergency override policy (§16).
 */

import {
  CircuitBreakerState,
  CircuitBreakerTrigger,
  EmergencyOverride,
  IncidentSeverity,
  Incident,
  KillSwitchAction,
  KillSwitchScope,
  OperatingMode,
  Role,
} from './types';

// ─── Circuit Breaker Manager (§15.1) ──────────────────────────────

export interface CircuitBreakerConfig {
  maxConsecutiveFailures: number;
  oracleDriftThresholdMs: number;
  marketAnomalyScoreThreshold: number;
  slippageBreachThresholdBps: number;
}

const DEFAULT_CIRCUIT_BREAKER_CONFIG: CircuitBreakerConfig = {
  maxConsecutiveFailures: 3,
  oracleDriftThresholdMs: 300_000, // 5 minutes
  marketAnomalyScoreThreshold: 85,
  slippageBreachThresholdBps: 500, // 5%
};

export class CircuitBreakerManager {
  private state: CircuitBreakerState = { triggered: false };
  private consecutiveFailures = 0;
  private killSwitches: KillSwitchAction[] = [];
  private incidents: Incident[] = [];
  private config: CircuitBreakerConfig;
  private onModeChange?: (mode: OperatingMode) => void;

  constructor(
    config: CircuitBreakerConfig = DEFAULT_CIRCUIT_BREAKER_CONFIG,
    onModeChange?: (mode: OperatingMode) => void,
  ) {
    this.config = config;
    this.onModeChange = onModeChange;
  }

  /** Record an execution failure */
  recordFailure(): CircuitBreakerState {
    this.consecutiveFailures++;
    if (this.consecutiveFailures >= this.config.maxConsecutiveFailures) {
      return this.trip(CircuitBreakerTrigger.RepeatedFailedExecutions);
    }
    return this.state;
  }

  /** Record a successful execution (resets failure counter) */
  recordSuccess(): void {
    this.consecutiveFailures = 0;
  }

  /** Check oracle consistency */
  checkOracleHealth(driftMs: number): CircuitBreakerState {
    if (driftMs > this.config.oracleDriftThresholdMs) {
      return this.trip(CircuitBreakerTrigger.OracleInconsistency);
    }
    return this.state;
  }

  /** Check market anomaly score */
  checkMarketAnomaly(score: number): CircuitBreakerState {
    if (score > this.config.marketAnomalyScoreThreshold) {
      return this.trip(CircuitBreakerTrigger.MarketAnomalyScore);
    }
    return this.state;
  }

  /** Check signer policy match */
  reportSignerPolicyMismatch(): CircuitBreakerState {
    return this.trip(CircuitBreakerTrigger.SignerPolicyMismatch);
  }

  /** Check route slippage */
  checkSlippage(actualBps: number): CircuitBreakerState {
    if (actualBps > this.config.slippageBreachThresholdBps) {
      return this.trip(CircuitBreakerTrigger.RouteSlippageBreach);
    }
    return this.state;
  }

  /** Report RPC consensus failure */
  reportRPCFailure(): CircuitBreakerState {
    return this.trip(CircuitBreakerTrigger.RPCConsensusFailure);
  }

  /** Trip the circuit breaker */
  private trip(trigger: CircuitBreakerTrigger): CircuitBreakerState {
    this.state = {
      triggered: true,
      trigger,
      triggeredAt: Date.now(),
      message: `Circuit breaker tripped: ${trigger}`,
    };

    // Switch to degraded safe mode
    this.onModeChange?.(OperatingMode.DegradedSafe);

    // Create incident
    this.createIncident(
      trigger === CircuitBreakerTrigger.RepeatedFailedExecutions
        ? IncidentSeverity.Sev2_ExecutionBlockedOrInconsistent
        : IncidentSeverity.Sev3_AdvisoryDegradationOnly,
      `Circuit breaker: ${trigger}`,
    );

    return this.state;
  }

  /** Reset the circuit breaker (manual action) */
  reset(): void {
    this.state = { triggered: false };
    this.consecutiveFailures = 0;
  }

  /** Get current circuit breaker state */
  getState(): CircuitBreakerState {
    return { ...this.state };
  }

  isTripped(): boolean {
    return this.state.triggered;
  }

  // ─── Kill Switches (§15.2) ──────────────────────────────────────

  activateKillSwitch(params: {
    scope: KillSwitchScope;
    target?: string;
    activatedBy: string;
    reason: string;
  }): KillSwitchAction {
    const action: KillSwitchAction = {
      scope: params.scope,
      target: params.target,
      activatedBy: params.activatedBy,
      activatedAt: Date.now(),
      reason: params.reason,
    };
    this.killSwitches.push(action);

    if (params.scope === KillSwitchScope.AllExecution) {
      this.onModeChange?.(OperatingMode.DegradedSafe);
    }

    return action;
  }

  deactivateKillSwitch(scope: KillSwitchScope, target?: string): boolean {
    const idx = this.killSwitches.findIndex(
      ks => ks.scope === scope && ks.target === target,
    );
    if (idx >= 0) {
      this.killSwitches.splice(idx, 1);
      return true;
    }
    return false;
  }

  isKillSwitchActive(scope: KillSwitchScope, target?: string): boolean {
    // All-execution kill switch blocks everything
    if (this.killSwitches.some(ks => ks.scope === KillSwitchScope.AllExecution)) {
      return true;
    }
    return this.killSwitches.some(
      ks => ks.scope === scope && (!target || ks.target === target),
    );
  }

  getActiveKillSwitches(): KillSwitchAction[] {
    return [...this.killSwitches];
  }

  // ─── Incident Management (§18) ─────────────────────────────────

  createIncident(
    severity: IncidentSeverity,
    description: string,
    affectedPath?: string,
  ): Incident {
    const incident: Incident = {
      incidentId: `INC-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      severity,
      description,
      affectedPath,
      snapshots: [],
      createdAt: Date.now(),
      requiresPostmortem:
        severity === IncidentSeverity.Sev1_FundsOrRightsAtRisk ||
        severity === IncidentSeverity.Sev2_ExecutionBlockedOrInconsistent,
    };
    this.incidents.push(incident);
    return incident;
  }

  resolveIncident(incidentId: string): boolean {
    const incident = this.incidents.find(i => i.incidentId === incidentId);
    if (incident && !incident.resolvedAt) {
      incident.resolvedAt = Date.now();
      return true;
    }
    return false;
  }

  getOpenIncidents(): Incident[] {
    return this.incidents.filter(i => !i.resolvedAt);
  }

  // ─── Emergency Override (§16) ───────────────────────────────────

  validateEmergencyOverride(override: EmergencyOverride, now: number): {
    valid: boolean;
    reason: string;
  } {
    // Dual approval minimum
    if (override.approvals.length < 2) {
      return { valid: false, reason: 'Emergency override requires dual approval minimum' };
    }

    // Must have explicit reason
    if (!override.reason || override.reason.trim().length === 0) {
      return { valid: false, reason: 'Emergency override requires explicit reason' };
    }

    // Must have scope-limited duration
    if (override.scopeDurationMs <= 0) {
      return { valid: false, reason: 'Emergency override requires scope-limited duration' };
    }

    // Check if expired
    if (override.expiresAt <= now) {
      return { valid: false, reason: 'Emergency override has expired' };
    }

    // Postmortem must be required
    if (!override.postmortemRequired) {
      return { valid: false, reason: 'Emergency override must require postmortem' };
    }

    return { valid: true, reason: 'Emergency override validated' };
  }
}
