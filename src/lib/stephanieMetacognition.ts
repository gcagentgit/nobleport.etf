/**
 * Stephanie.ai Metacognition & Memory Engine
 *
 * Provides self-reflective reasoning, persistent memory, and
 * "needs more memory" detection for the Stephanie.ai orchestration hub.
 *
 * @domain stephanie.ai / stephanie.io
 * @ens stephanie.nobleport.eth
 */

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

export type ConfidenceLevel = 'very_low' | 'low' | 'moderate' | 'high' | 'very_high';
export type ReasoningPhase = 'perceiving' | 'analyzing' | 'deciding' | 'executing' | 'reflecting';
export type MemoryType = 'episodic' | 'semantic' | 'procedural' | 'working';

export interface ReasoningTrace {
  id: string;
  timestamp: Date;
  phase: ReasoningPhase;
  taskId: string;
  thought: string;
  confidence: number;          // 0.0 – 1.0
  alternatives: string[];
  chosenAction: string;
  rationale: string;
  outcome?: 'success' | 'partial' | 'failure';
  reflectionNotes?: string;
}

export interface MemoryEntry {
  id: string;
  type: MemoryType;
  createdAt: Date;
  lastAccessed: Date;
  accessCount: number;
  content: string;
  context: Record<string, unknown>;
  tags: string[];
  importance: number;          // 0.0 – 1.0
  decay: number;               // 0.0 – 1.0 (1 = fully retained)
  associations: string[];      // IDs of related memories
}

export interface MetacognitiveState {
  currentPhase: ReasoningPhase;
  overallConfidence: number;
  activeThoughts: string[];
  uncertainties: string[];
  knowledgeGaps: string[];
  selfAssessment: string;
}

export interface MemoryPressure {
  totalMemories: number;
  workingMemoryUsed: number;
  workingMemoryCapacity: number;
  utilizationPercent: number;
  needsMoreMemory: boolean;
  recommendation: string;
  decayedCount: number;
  criticalMemories: number;
}

export interface MemoryStats {
  total: number;
  byType: Record<MemoryType, number>;
  averageImportance: number;
  averageDecay: number;
  oldestMemory: Date | null;
  newestMemory: Date | null;
  pressure: MemoryPressure;
}

export interface MetacognitionConfig {
  workingMemoryCapacity: number;         // max items in working memory
  memoryDecayRate: number;               // decay per hour (0.0 – 1.0)
  confidenceThreshold: number;           // below this triggers reflection
  memoryPressureThreshold: number;       // % utilization that triggers warning
  maxReasoningTraces: number;            // max traces to retain
  enableAutoReflection: boolean;
}

// ============================================================================
// DEFAULT CONFIGURATION
// ============================================================================

const DEFAULT_CONFIG: MetacognitionConfig = {
  workingMemoryCapacity: 128,
  memoryDecayRate: 0.02,
  confidenceThreshold: 0.6,
  memoryPressureThreshold: 80,
  maxReasoningTraces: 500,
  enableAutoReflection: true,
};

// ============================================================================
// METACOGNITION ENGINE
// ============================================================================

export class MetacognitionEngine {
  private config: MetacognitionConfig;
  private reasoningTraces: ReasoningTrace[] = [];
  private currentState: MetacognitiveState;

  constructor(config?: Partial<MetacognitionConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.currentState = {
      currentPhase: 'perceiving',
      overallConfidence: 1.0,
      activeThoughts: [],
      uncertainties: [],
      knowledgeGaps: [],
      selfAssessment: 'Initialized — awaiting first task.',
    };
  }

  // ----- Phase management -----

  setPhase(phase: ReasoningPhase): void {
    this.currentState.currentPhase = phase;
  }

  getState(): MetacognitiveState {
    return { ...this.currentState };
  }

  // ----- Reasoning traces -----

  recordThought(params: {
    taskId: string;
    phase: ReasoningPhase;
    thought: string;
    confidence: number;
    alternatives: string[];
    chosenAction: string;
    rationale: string;
  }): ReasoningTrace {
    const trace: ReasoningTrace = {
      id: `trace_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      timestamp: new Date(),
      ...params,
    };

    this.reasoningTraces.push(trace);

    // Trim old traces if exceeding capacity
    if (this.reasoningTraces.length > this.config.maxReasoningTraces) {
      this.reasoningTraces = this.reasoningTraces.slice(-this.config.maxReasoningTraces);
    }

    // Update state
    this.currentState.activeThoughts.push(params.thought);
    if (this.currentState.activeThoughts.length > 10) {
      this.currentState.activeThoughts = this.currentState.activeThoughts.slice(-10);
    }
    this.currentState.overallConfidence = this.computeOverallConfidence();

    // Auto-reflection when confidence drops
    if (this.config.enableAutoReflection && params.confidence < this.config.confidenceThreshold) {
      this.currentState.uncertainties.push(
        `Low confidence (${(params.confidence * 100).toFixed(0)}%) on: ${params.thought}`
      );
    }

    return trace;
  }

  recordOutcome(traceId: string, outcome: 'success' | 'partial' | 'failure', notes?: string): void {
    const trace = this.reasoningTraces.find(t => t.id === traceId);
    if (trace) {
      trace.outcome = outcome;
      trace.reflectionNotes = notes;
    }
  }

  getTraces(filter?: { taskId?: string; phase?: ReasoningPhase; limit?: number }): ReasoningTrace[] {
    let results = [...this.reasoningTraces];
    if (filter?.taskId) results = results.filter(t => t.taskId === filter.taskId);
    if (filter?.phase) results = results.filter(t => t.phase === filter.phase);
    if (filter?.limit) results = results.slice(-filter.limit);
    return results;
  }

  // ----- Self-assessment -----

  reflect(): string {
    const recent = this.reasoningTraces.slice(-20);
    if (recent.length === 0) {
      this.currentState.selfAssessment = 'No reasoning history yet — ready to begin.';
      return this.currentState.selfAssessment;
    }

    const avgConf = recent.reduce((s, t) => s + t.confidence, 0) / recent.length;
    const successes = recent.filter(t => t.outcome === 'success').length;
    const failures = recent.filter(t => t.outcome === 'failure').length;
    const pending = recent.filter(t => !t.outcome).length;

    const gaps = this.identifyKnowledgeGaps(recent);
    this.currentState.knowledgeGaps = gaps;

    let assessment: string;
    if (avgConf >= 0.8 && failures === 0) {
      assessment = `Operating at high confidence (${(avgConf * 100).toFixed(0)}%). ${successes} successes in recent history. Systems nominal.`;
    } else if (avgConf >= 0.5) {
      assessment = `Moderate confidence (${(avgConf * 100).toFixed(0)}%). ${successes} successes, ${failures} failures, ${pending} pending. ${gaps.length} knowledge gap(s) detected.`;
    } else {
      assessment = `Low confidence (${(avgConf * 100).toFixed(0)}%). ${failures} failures detected. ${gaps.length} knowledge gap(s) require attention. Recommend human review.`;
    }

    this.currentState.selfAssessment = assessment;
    this.currentState.overallConfidence = avgConf;
    return assessment;
  }

  addUncertainty(uncertainty: string): void {
    this.currentState.uncertainties.push(uncertainty);
    if (this.currentState.uncertainties.length > 20) {
      this.currentState.uncertainties = this.currentState.uncertainties.slice(-20);
    }
  }

  clearUncertainties(): void {
    this.currentState.uncertainties = [];
  }

  // ----- Private helpers -----

  private computeOverallConfidence(): number {
    const recent = this.reasoningTraces.slice(-10);
    if (recent.length === 0) return 1.0;
    return recent.reduce((s, t) => s + t.confidence, 0) / recent.length;
  }

  private identifyKnowledgeGaps(traces: ReasoningTrace[]): string[] {
    const gaps: string[] = [];
    const lowConfTraces = traces.filter(t => t.confidence < this.config.confidenceThreshold);

    for (const trace of lowConfTraces) {
      if (trace.alternatives.length > 2) {
        gaps.push(`Ambiguous decision space for task ${trace.taskId}: ${trace.thought}`);
      }
      if (trace.outcome === 'failure') {
        gaps.push(`Failed reasoning in ${trace.phase} phase: ${trace.rationale}`);
      }
    }

    return [...new Set(gaps)];
  }
}

// ============================================================================
// MEMORY STORE
// ============================================================================

export class MemoryStore {
  private memories: Map<string, MemoryEntry> = new Map();
  private config: MetacognitionConfig;

  constructor(config?: Partial<MetacognitionConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  // ----- CRUD -----

  store(params: {
    type: MemoryType;
    content: string;
    context?: Record<string, unknown>;
    tags?: string[];
    importance?: number;
    associations?: string[];
  }): MemoryEntry {
    const entry: MemoryEntry = {
      id: `mem_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      type: params.type,
      createdAt: new Date(),
      lastAccessed: new Date(),
      accessCount: 0,
      content: params.content,
      context: params.context || {},
      tags: params.tags || [],
      importance: params.importance ?? 0.5,
      decay: 1.0,
      associations: params.associations || [],
    };

    this.memories.set(entry.id, entry);
    return entry;
  }

  recall(id: string): MemoryEntry | undefined {
    const entry = this.memories.get(id);
    if (entry) {
      entry.lastAccessed = new Date();
      entry.accessCount += 1;
      // Accessing a memory reinforces it
      entry.decay = Math.min(1.0, entry.decay + 0.1);
    }
    return entry;
  }

  forget(id: string): boolean {
    return this.memories.delete(id);
  }

  // ----- Search -----

  search(query: {
    type?: MemoryType;
    tags?: string[];
    minImportance?: number;
    keyword?: string;
    limit?: number;
  }): MemoryEntry[] {
    let results = Array.from(this.memories.values());

    if (query.type) results = results.filter(m => m.type === query.type);
    if (query.tags && query.tags.length > 0) {
      results = results.filter(m => query.tags!.some(t => m.tags.includes(t)));
    }
    if (query.minImportance !== undefined) {
      results = results.filter(m => m.importance >= query.minImportance!);
    }
    if (query.keyword) {
      const kw = query.keyword.toLowerCase();
      results = results.filter(m => m.content.toLowerCase().includes(kw));
    }

    // Sort by relevance: importance * decay * recency
    results.sort((a, b) => {
      const scoreA = a.importance * a.decay;
      const scoreB = b.importance * b.decay;
      return scoreB - scoreA;
    });

    if (query.limit) results = results.slice(0, query.limit);
    return results;
  }

  getAll(): MemoryEntry[] {
    return Array.from(this.memories.values());
  }

  // ----- Memory decay -----

  applyDecay(): void {
    const now = Date.now();
    for (const entry of this.memories.values()) {
      const hoursElapsed = (now - entry.lastAccessed.getTime()) / (1000 * 60 * 60);
      const decayAmount = this.config.memoryDecayRate * hoursElapsed;
      entry.decay = Math.max(0, entry.decay - decayAmount);
    }
  }

  pruneDecayed(threshold: number = 0.1): MemoryEntry[] {
    const pruned: MemoryEntry[] = [];
    for (const [id, entry] of this.memories) {
      if (entry.decay < threshold && entry.importance < 0.8) {
        pruned.push(entry);
        this.memories.delete(id);
      }
    }
    return pruned;
  }

  // ----- Memory pressure / "needs more memory" -----

  getMemoryPressure(): MemoryPressure {
    const total = this.memories.size;
    const workingCount = Array.from(this.memories.values())
      .filter(m => m.type === 'working').length;
    const capacity = this.config.workingMemoryCapacity;
    const utilization = total > 0 ? (workingCount / capacity) * 100 : 0;
    const needsMore = utilization >= this.config.memoryPressureThreshold;
    const decayed = Array.from(this.memories.values()).filter(m => m.decay < 0.3).length;
    const critical = Array.from(this.memories.values()).filter(m => m.importance >= 0.9).length;

    let recommendation: string;
    if (utilization >= 95) {
      recommendation = 'CRITICAL: Working memory at capacity. Prune low-priority memories or expand capacity immediately.';
    } else if (utilization >= this.config.memoryPressureThreshold) {
      recommendation = `WARNING: Working memory at ${utilization.toFixed(0)}%. Consider archiving ${decayed} decayed memories to long-term storage.`;
    } else if (utilization >= 50) {
      recommendation = `MODERATE: Memory utilization at ${utilization.toFixed(0)}%. Operating within normal parameters.`;
    } else {
      recommendation = `HEALTHY: Memory utilization at ${utilization.toFixed(0)}%. Ample capacity available.`;
    }

    return {
      totalMemories: total,
      workingMemoryUsed: workingCount,
      workingMemoryCapacity: capacity,
      utilizationPercent: Math.round(utilization),
      needsMoreMemory: needsMore,
      recommendation,
      decayedCount: decayed,
      criticalMemories: critical,
    };
  }

  // ----- Stats -----

  getStats(): MemoryStats {
    const all = Array.from(this.memories.values());
    const byType: Record<MemoryType, number> = {
      episodic: 0,
      semantic: 0,
      procedural: 0,
      working: 0,
    };
    for (const m of all) byType[m.type]++;

    const avgImportance = all.length > 0
      ? all.reduce((s, m) => s + m.importance, 0) / all.length
      : 0;
    const avgDecay = all.length > 0
      ? all.reduce((s, m) => s + m.decay, 0) / all.length
      : 0;

    const dates = all.map(m => m.createdAt.getTime());

    return {
      total: all.length,
      byType,
      averageImportance: avgImportance,
      averageDecay: avgDecay,
      oldestMemory: dates.length > 0 ? new Date(Math.min(...dates)) : null,
      newestMemory: dates.length > 0 ? new Date(Math.max(...dates)) : null,
      pressure: this.getMemoryPressure(),
    };
  }
}

// ============================================================================
// INTEGRATED METACOGNITION + MEMORY SYSTEM
// ============================================================================

export class StephanieMetacognition {
  public readonly metacognition: MetacognitionEngine;
  public readonly memory: MemoryStore;
  private config: MetacognitionConfig;

  constructor(config?: Partial<MetacognitionConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.metacognition = new MetacognitionEngine(this.config);
    this.memory = new MemoryStore(this.config);

    // Seed initial system memories
    this.seedSystemMemories();
  }

  private seedSystemMemories(): void {
    this.memory.store({
      type: 'semantic',
      content: 'Stephanie.ai is the AI orchestration hub for NoblePort.eth, managing 13 LLM platforms and 12 modules.',
      tags: ['system', 'identity', 'core'],
      importance: 1.0,
    });

    this.memory.store({
      type: 'procedural',
      content: 'Task routing: code-generation prefers Claude > ChatGPT > DeepSeek. Real-time analysis prefers Grok > Perplexity > Groq.',
      tags: ['routing', 'procedure', 'core'],
      importance: 0.95,
    });

    this.memory.store({
      type: 'semantic',
      content: 'All legal, medical, and financial decisions require human approval via HumanApprovalGateway smart contract. No AI bypass permitted.',
      tags: ['governance', 'compliance', 'critical'],
      importance: 1.0,
    });

    this.memory.store({
      type: 'procedural',
      content: 'ENS resolution: use did:ens method. Root identity is nobleport.eth. Stephanie identity is stephanie.nobleport.eth.',
      tags: ['identity', 'ens', 'procedure'],
      importance: 0.9,
    });
  }

  // ----- High-level operations -----

  /**
   * Process a task with full metacognitive tracking:
   * perceive -> analyze -> decide -> execute -> reflect
   */
  beginTask(taskId: string, description: string): ReasoningTrace {
    this.metacognition.setPhase('perceiving');

    // Store as episodic memory
    this.memory.store({
      type: 'episodic',
      content: `Task started: ${description}`,
      context: { taskId },
      tags: ['task', 'start'],
      importance: 0.6,
    });

    // Record the initial perception
    return this.metacognition.recordThought({
      taskId,
      phase: 'perceiving',
      thought: `Received task: ${description}`,
      confidence: 0.8,
      alternatives: [],
      chosenAction: 'Begin analysis',
      rationale: 'New task received, entering analysis phase.',
    });
  }

  analyzeTask(taskId: string, analysis: string, confidence: number, alternatives: string[]): ReasoningTrace {
    this.metacognition.setPhase('analyzing');

    return this.metacognition.recordThought({
      taskId,
      phase: 'analyzing',
      thought: analysis,
      confidence,
      alternatives,
      chosenAction: alternatives[0] || 'Proceed with primary approach',
      rationale: `Analyzed ${alternatives.length} alternatives. Confidence: ${(confidence * 100).toFixed(0)}%.`,
    });
  }

  decideAction(taskId: string, decision: string, confidence: number, rationale: string): ReasoningTrace {
    this.metacognition.setPhase('deciding');

    // Store decision as working memory
    this.memory.store({
      type: 'working',
      content: `Decision for ${taskId}: ${decision}`,
      context: { taskId, confidence, rationale },
      tags: ['decision', 'active'],
      importance: 0.7,
    });

    return this.metacognition.recordThought({
      taskId,
      phase: 'deciding',
      thought: decision,
      confidence,
      alternatives: [],
      chosenAction: decision,
      rationale,
    });
  }

  completeTask(taskId: string, outcome: 'success' | 'partial' | 'failure', reflection: string): void {
    this.metacognition.setPhase('reflecting');

    // Record outcome on all traces for this task
    const traces = this.metacognition.getTraces({ taskId });
    for (const trace of traces) {
      if (!trace.outcome) {
        this.metacognition.recordOutcome(trace.id, outcome, reflection);
      }
    }

    // Store episodic memory of the outcome
    this.memory.store({
      type: 'episodic',
      content: `Task ${taskId} completed: ${outcome}. ${reflection}`,
      context: { taskId, outcome },
      tags: ['task', 'complete', outcome],
      importance: outcome === 'failure' ? 0.9 : 0.5,
    });

    // Learn from failures — store as procedural memory
    if (outcome === 'failure') {
      this.memory.store({
        type: 'procedural',
        content: `Lesson learned from ${taskId}: ${reflection}`,
        context: { taskId, outcome },
        tags: ['lesson', 'failure'],
        importance: 0.85,
      });
    }

    // Run self-reflection
    this.metacognition.reflect();
  }

  // ----- Combined status -----

  getFullStatus(): {
    metacognitive: MetacognitiveState;
    memoryStats: MemoryStats;
    needsMoreMemory: boolean;
    recentTraces: ReasoningTrace[];
  } {
    this.memory.applyDecay();
    const stats = this.memory.getStats();

    return {
      metacognitive: this.metacognition.getState(),
      memoryStats: stats,
      needsMoreMemory: stats.pressure.needsMoreMemory,
      recentTraces: this.metacognition.getTraces({ limit: 10 }),
    };
  }
}

// ============================================================================
// FACTORY
// ============================================================================

export function createMetacognition(config?: Partial<MetacognitionConfig>): StephanieMetacognition {
  return new StephanieMetacognition(config);
}

export default StephanieMetacognition;
