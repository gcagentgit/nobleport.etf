'use client';

import React, { useState, useEffect } from 'react';
import {
  StephanieAI,
  createStephanieAI,
  NOBLEPORT_MODULES,
  AI_PLATFORM_CONNECTIONS,
  MCPConnection,
  ModuleConnection
} from '../lib/stephanieAI';
import type {
  MetacognitiveState,
  MemoryStats,
  MemoryPressure,
  ReasoningTrace,
  MemoryEntry,
  ReasoningPhase,
} from '../lib/stephanieMetacognition';

/**
 * Stephanie.ai Network Hub Component
 *
 * Visual dashboard for managing AI platform connections and NoblePort module integrations
 * Provides real-time status monitoring and task orchestration interface
 */

// ============================================================================
// TYPES
// ============================================================================

interface PlatformCardProps {
  platform: MCPConnection;
  isSelected: boolean;
  onSelect: () => void;
}

interface ModuleCardProps {
  module: ModuleConnection;
  isSelected: boolean;
  onSelect: () => void;
}

interface NetworkStats {
  totalPlatforms: number;
  activePlatforms: number;
  totalModules: number;
  connectedModules: number;
  lastHealthCheck: Date | null;
  overallHealth: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
}

// ============================================================================
// METACOGNITION & MEMORY COMPONENTS
// ============================================================================

const PhaseIndicator: React.FC<{ phase: ReasoningPhase }> = ({ phase }) => {
  const phases: ReasoningPhase[] = ['perceiving', 'analyzing', 'deciding', 'executing', 'reflecting'];
  const phaseLabels: Record<ReasoningPhase, string> = {
    perceiving: 'Perceive',
    analyzing: 'Analyze',
    deciding: 'Decide',
    executing: 'Execute',
    reflecting: 'Reflect',
  };
  const phaseColors: Record<ReasoningPhase, string> = {
    perceiving: 'bg-blue-500',
    analyzing: 'bg-yellow-500',
    deciding: 'bg-purple-500',
    executing: 'bg-green-500',
    reflecting: 'bg-orange-500',
  };

  return (
    <div className="flex items-center gap-1">
      {phases.map((p) => (
        <div key={p} className="flex flex-col items-center">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white transition-all ${
              p === phase ? `${phaseColors[p]} ring-2 ring-white scale-110` : 'bg-gray-600 opacity-50'
            }`}
          >
            {phaseLabels[p][0]}
          </div>
          <span className={`text-[10px] mt-1 ${p === phase ? 'text-white font-semibold' : 'text-gray-500'}`}>
            {phaseLabels[p]}
          </span>
        </div>
      ))}
    </div>
  );
};

const ConfidenceMeter: React.FC<{ confidence: number }> = ({ confidence }) => {
  const pct = Math.round(confidence * 100);
  const color = pct >= 80 ? 'bg-green-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-400">Confidence</span>
        <span className="text-white font-mono">{pct}%</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-3">
        <div className={`${color} h-3 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
};

const MemoryPressureGauge: React.FC<{ pressure: MemoryPressure }> = ({ pressure }) => {
  const pct = pressure.utilizationPercent;
  const needsMore = pressure.needsMoreMemory;
  const gaugeColor = pct >= 95 ? 'bg-red-600' : pct >= 80 ? 'bg-orange-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-green-500';
  const borderPulse = needsMore ? 'border-red-500 animate-pulse' : 'border-purple-500/30';

  return (
    <div className={`bg-white/5 rounded-lg p-5 border-2 ${borderPulse}`}>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-white font-semibold">Memory Pressure</h4>
        {needsMore && (
          <span className="bg-red-600 text-white text-xs font-bold px-3 py-1 rounded-full animate-pulse">
            NEEDS MORE MEMORY
          </span>
        )}
      </div>
      <div className="w-full bg-gray-700 rounded-full h-5 mb-3">
        <div className={`${gaugeColor} h-5 rounded-full transition-all flex items-center justify-center`} style={{ width: `${Math.min(pct, 100)}%` }}>
          {pct >= 20 && <span className="text-xs font-bold text-white">{pct}%</span>}
        </div>
      </div>
      <p className="text-sm text-gray-300 mb-3">{pressure.recommendation}</p>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="bg-black/30 rounded p-2">
          <span className="text-gray-400">Working Memory</span>
          <p className="text-white font-mono">{pressure.workingMemoryUsed} / {pressure.workingMemoryCapacity}</p>
        </div>
        <div className="bg-black/30 rounded p-2">
          <span className="text-gray-400">Total Memories</span>
          <p className="text-white font-mono">{pressure.totalMemories}</p>
        </div>
        <div className="bg-black/30 rounded p-2">
          <span className="text-gray-400">Decayed</span>
          <p className="text-yellow-400 font-mono">{pressure.decayedCount}</p>
        </div>
        <div className="bg-black/30 rounded p-2">
          <span className="text-gray-400">Critical</span>
          <p className="text-red-400 font-mono">{pressure.criticalMemories}</p>
        </div>
      </div>
    </div>
  );
};

const TraceCard: React.FC<{ trace: ReasoningTrace }> = ({ trace }) => {
  const outcomeColor: Record<string, string> = {
    success: 'text-green-400',
    partial: 'text-yellow-400',
    failure: 'text-red-400',
  };

  return (
    <div className="bg-black/30 rounded-lg p-3 border border-purple-500/20">
      <div className="flex justify-between items-start mb-1">
        <span className="text-xs bg-purple-500/30 text-purple-300 px-2 py-0.5 rounded">{trace.phase}</span>
        <span className="text-xs text-gray-500">{trace.timestamp.toLocaleTimeString()}</span>
      </div>
      <p className="text-sm text-white mt-2">{trace.thought}</p>
      <div className="flex items-center gap-3 mt-2 text-xs">
        <span className="text-gray-400">Confidence: <span className="text-white font-mono">{(trace.confidence * 100).toFixed(0)}%</span></span>
        {trace.outcome && (
          <span className={outcomeColor[trace.outcome] || 'text-gray-400'}>
            {trace.outcome.toUpperCase()}
          </span>
        )}
      </div>
      {trace.reflectionNotes && (
        <p className="text-xs text-gray-400 mt-1 italic">{trace.reflectionNotes}</p>
      )}
    </div>
  );
};

const MemoryTypeBreakdown: React.FC<{ stats: MemoryStats }> = ({ stats }) => {
  const typeColors: Record<string, string> = {
    episodic: 'bg-blue-500',
    semantic: 'bg-green-500',
    procedural: 'bg-purple-500',
    working: 'bg-orange-500',
  };

  return (
    <div className="bg-white/5 rounded-lg p-5 border border-purple-500/30">
      <h4 className="text-white font-semibold mb-3">Memory Breakdown</h4>
      <div className="space-y-3">
        {(Object.entries(stats.byType) as [string, number][]).map(([type, count]) => (
          <div key={type}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-300 capitalize">{type}</span>
              <span className="text-white font-mono">{count}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className={`${typeColors[type] || 'bg-gray-500'} h-2 rounded-full transition-all`}
                style={{ width: stats.total > 0 ? `${(count / stats.total) * 100}%` : '0%' }}
              />
            </div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-3 mt-4 text-xs">
        <div className="bg-black/30 rounded p-2">
          <span className="text-gray-400">Avg Importance</span>
          <p className="text-white font-mono">{(stats.averageImportance * 100).toFixed(0)}%</p>
        </div>
        <div className="bg-black/30 rounded p-2">
          <span className="text-gray-400">Avg Retention</span>
          <p className="text-white font-mono">{(stats.averageDecay * 100).toFixed(0)}%</p>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// HELPER COMPONENTS
// ============================================================================

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const colorMap: Record<string, string> = {
    active: 'bg-green-500',
    connected: 'bg-green-500',
    healthy: 'bg-green-500',
    pending: 'bg-yellow-500',
    degraded: 'bg-yellow-500',
    disabled: 'bg-gray-500',
    disconnected: 'bg-red-500',
    unhealthy: 'bg-red-500',
    unknown: 'bg-gray-400'
  };

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white ${colorMap[status] || 'bg-gray-500'}`}>
      {status}
    </span>
  );
};

const PlatformCard: React.FC<PlatformCardProps> = ({ platform, isSelected, onSelect }) => {
  const providerColors: Record<string, string> = {
    'Anthropic': 'border-orange-500 bg-orange-50',
    'OpenAI': 'border-green-500 bg-green-50',
    'xAI': 'border-blue-500 bg-blue-50',
    'Google': 'border-red-500 bg-red-50',
    'Meta': 'border-blue-600 bg-blue-50',
    'Replit': 'border-orange-400 bg-orange-50',
    'Mistral': 'border-purple-500 bg-purple-50',
    'Cohere': 'border-pink-500 bg-pink-50',
    'Perplexity': 'border-teal-500 bg-teal-50',
    'Hugging Face': 'border-yellow-500 bg-yellow-50',
    'Together': 'border-indigo-500 bg-indigo-50',
    'Groq': 'border-cyan-500 bg-cyan-50',
    'DeepSeek': 'border-emerald-500 bg-emerald-50'
  };

  const borderColor = providerColors[platform.provider] || 'border-gray-500 bg-gray-50';

  return (
    <div
      onClick={onSelect}
      className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${borderColor} ${
        isSelected ? 'ring-2 ring-offset-2 ring-blue-500 shadow-lg' : 'hover:shadow-md'
      }`}
    >
      <div className="flex justify-between items-start mb-2">
        <h4 className="font-semibold text-gray-900">{platform.name}</h4>
        <StatusBadge status={platform.status} />
      </div>
      <p className="text-xs text-gray-600 mb-2">{platform.provider}</p>
      <div className="flex flex-wrap gap-1">
        {platform.capabilities.slice(0, 3).map((cap, idx) => (
          <span key={idx} className="text-xs bg-white px-2 py-0.5 rounded border">
            {cap}
          </span>
        ))}
        {platform.capabilities.length > 3 && (
          <span className="text-xs text-gray-500">+{platform.capabilities.length - 3} more</span>
        )}
      </div>
    </div>
  );
};

const ModuleCard: React.FC<ModuleCardProps> = ({ module, isSelected, onSelect }) => {
  return (
    <div
      onClick={onSelect}
      className={`p-4 rounded-lg border-2 cursor-pointer transition-all bg-white ${
        isSelected ? 'border-blue-500 ring-2 ring-offset-2 ring-blue-500 shadow-lg' : 'border-gray-200 hover:border-gray-400 hover:shadow-md'
      }`}
    >
      <div className="flex justify-between items-start mb-2">
        <h4 className="font-semibold text-gray-900 text-sm">{module.module.replace(/_/g, ' ')}</h4>
        <StatusBadge status={module.status} />
      </div>
      <p className="text-xs text-gray-500 font-mono mb-2">{module.ens}</p>
      <div className="flex flex-wrap gap-1">
        {module.capabilities.slice(0, 2).map((cap, idx) => (
          <span key={idx} className="text-xs bg-gray-100 px-2 py-0.5 rounded">
            {cap}
          </span>
        ))}
        {module.capabilities.length > 2 && (
          <span className="text-xs text-gray-500">+{module.capabilities.length - 2}</span>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const StephanieAINetworkHub: React.FC = () => {
  const [stephanie, setStephanie] = useState<StephanieAI | null>(null);
  const [platforms, setPlatforms] = useState<MCPConnection[]>([]);
  const [modules, setModules] = useState<ModuleConnection[]>([]);
  const [selectedPlatform, setSelectedPlatform] = useState<MCPConnection | null>(null);
  const [selectedModule, setSelectedModule] = useState<ModuleConnection | null>(null);
  const [stats, setStats] = useState<NetworkStats>({
    totalPlatforms: 0,
    activePlatforms: 0,
    totalModules: 0,
    connectedModules: 0,
    lastHealthCheck: null,
    overallHealth: 'unknown'
  });
  const [metacogState, setMetacogState] = useState<MetacognitiveState | null>(null);
  const [memoryStats, setMemoryStats] = useState<MemoryStats | null>(null);
  const [memoryPressure, setMemoryPressure] = useState<MemoryPressure | null>(null);
  const [recentTraces, setRecentTraces] = useState<ReasoningTrace[]>([]);
  const [isInitializing, setIsInitializing] = useState(true);
  const [activeTab, setActiveTab] = useState<'platforms' | 'modules' | 'metacognition' | 'architecture'>('platforms');

  // Initialize Stephanie.ai
  useEffect(() => {
    const initStephanie = async () => {
      try {
        const instance = createStephanieAI();
        await instance.initialize();

        setStephanie(instance);
        setPlatforms(instance.getConnectedPlatforms());
        setModules(instance.getConnectedModules());

        const health = await instance.healthCheck();

        setStats({
          totalPlatforms: AI_PLATFORM_CONNECTIONS.length,
          activePlatforms: instance.getConnectedPlatforms().filter(p => p.status === 'active').length,
          totalModules: Object.keys(NOBLEPORT_MODULES.MODULES).length,
          connectedModules: instance.getConnectedModules().filter(m => m.status === 'connected').length,
          lastHealthCheck: new Date(),
          overallHealth: health.overall
        });

        // Initialize metacognition state
        setMetacogState(instance.getMetacognitiveState());
        setMemoryStats(instance.getMemoryStats());
        setMemoryPressure(instance.getMemoryPressure());
        setRecentTraces(instance.getRecentTraces(10));
      } catch (error) {
        console.error('Failed to initialize Stephanie.ai:', error);
      } finally {
        setIsInitializing(false);
      }
    };

    initStephanie();
  }, []);

  // Render loading state
  if (isInitializing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold text-white mb-2">Initializing Stephanie.ai</h2>
          <p className="text-purple-300">Connecting to NoblePort.eth network...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-sm border-b border-purple-500/30">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">
                Stephanie<span className="text-purple-400">.ai</span>
              </h1>
              <p className="text-purple-300 text-sm mt-1">
                AI Network Hub for NoblePort.eth
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-xs text-gray-400">Network Status</p>
                <StatusBadge status={stats.overallHealth} />
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-400">ENS Identity</p>
                <p className="text-sm text-white font-mono">stephanie.nobleport.eth</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Stats Bar */}
      <div className="bg-black/20 border-b border-purple-500/20">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-gray-400 text-xs uppercase tracking-wider">AI Platforms</p>
              <p className="text-2xl font-bold text-white">
                {stats.activePlatforms}<span className="text-gray-500">/{stats.totalPlatforms}</span>
              </p>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-gray-400 text-xs uppercase tracking-wider">NoblePort Modules</p>
              <p className="text-2xl font-bold text-white">
                {stats.connectedModules}<span className="text-gray-500">/{stats.totalModules}</span>
              </p>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-gray-400 text-xs uppercase tracking-wider">Root Identity</p>
              <p className="text-lg font-mono text-purple-400">nobleport.eth</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-gray-400 text-xs uppercase tracking-wider">DID Method</p>
              <p className="text-lg font-mono text-purple-400">did:ens</p>
            </div>
            <div className={`rounded-lg p-4 ${memoryPressure?.needsMoreMemory ? 'bg-red-900/40 border border-red-500 animate-pulse' : 'bg-white/5'}`}>
              <p className="text-gray-400 text-xs uppercase tracking-wider">Memory Status</p>
              {memoryPressure?.needsMoreMemory ? (
                <p className="text-lg font-bold text-red-400">NEEDS MORE MEMORY</p>
              ) : (
                <p className="text-lg font-mono text-green-400">{memoryPressure?.utilizationPercent ?? 0}% used</p>
              )}
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-gray-400 text-xs uppercase tracking-wider">Confidence</p>
              <p className={`text-lg font-mono ${
                (metacogState?.overallConfidence ?? 1) >= 0.8 ? 'text-green-400' :
                (metacogState?.overallConfidence ?? 1) >= 0.5 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {((metacogState?.overallConfidence ?? 1) * 100).toFixed(0)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 pt-6">
        <div className="flex gap-2 border-b border-purple-500/30">
          {(['platforms', 'modules', 'metacognition', 'architecture'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 font-medium transition-all relative ${
                activeTab === tab
                  ? 'text-white border-b-2 border-purple-500 bg-purple-500/10'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {tab === 'platforms' && 'AI Platforms'}
              {tab === 'modules' && 'NoblePort Modules'}
              {tab === 'metacognition' && (
                <>
                  Metacognition & Memory
                  {memoryPressure?.needsMoreMemory && (
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                  )}
                </>
              )}
              {tab === 'architecture' && 'Network Architecture'}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* AI Platforms Tab */}
        {activeTab === 'platforms' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <h2 className="text-xl font-semibold text-white mb-4">Connected AI Platforms (MCP)</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {platforms.map((platform) => (
                  <PlatformCard
                    key={platform.id}
                    platform={platform}
                    isSelected={selectedPlatform?.id === platform.id}
                    onSelect={() => setSelectedPlatform(platform)}
                  />
                ))}
              </div>
            </div>

            {/* Platform Details */}
            <div className="bg-white/5 rounded-lg p-6 border border-purple-500/30">
              <h3 className="text-lg font-semibold text-white mb-4">Platform Details</h3>
              {selectedPlatform ? (
                <div className="space-y-4">
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider">Name</p>
                    <p className="text-white font-semibold">{selectedPlatform.name}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider">Provider</p>
                    <p className="text-white">{selectedPlatform.provider}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider">Protocol</p>
                    <p className="text-purple-400 font-mono">{selectedPlatform.protocol}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider">Endpoint</p>
                    <p className="text-purple-400 font-mono text-sm break-all">{selectedPlatform.endpoint}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Capabilities</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedPlatform.capabilities.map((cap, idx) => (
                        <span key={idx} className="text-xs bg-purple-500/20 text-purple-300 px-2 py-1 rounded">
                          {cap}
                        </span>
                      ))}
                    </div>
                  </div>
                  {selectedPlatform.rateLimits && (
                    <div>
                      <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Rate Limits</p>
                      <p className="text-sm text-gray-300">
                        {selectedPlatform.rateLimits.requestsPerMinute} req/min
                      </p>
                      <p className="text-sm text-gray-300">
                        {selectedPlatform.rateLimits.tokensPerRequest.toLocaleString()} tokens/req
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-gray-400">Select a platform to view details</p>
              )}
            </div>
          </div>
        )}

        {/* NoblePort Modules Tab */}
        {activeTab === 'modules' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <h2 className="text-xl font-semibold text-white mb-4">NoblePort.eth Modules</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {modules.map((module) => (
                  <ModuleCard
                    key={module.module}
                    module={module}
                    isSelected={selectedModule?.module === module.module}
                    onSelect={() => setSelectedModule(module)}
                  />
                ))}
              </div>
            </div>

            {/* Module Details */}
            <div className="bg-white/5 rounded-lg p-6 border border-purple-500/30">
              <h3 className="text-lg font-semibold text-white mb-4">Module Details</h3>
              {selectedModule ? (
                <div className="space-y-4">
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider">Module</p>
                    <p className="text-white font-semibold">{selectedModule.module.replace(/_/g, ' ')}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider">ENS Name</p>
                    <p className="text-purple-400 font-mono">{selectedModule.ens}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider">DID</p>
                    <p className="text-purple-400 font-mono text-sm break-all">{selectedModule.did}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider">Status</p>
                    <StatusBadge status={selectedModule.status} />
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Capabilities</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedModule.capabilities.map((cap, idx) => (
                        <span key={idx} className="text-xs bg-purple-500/20 text-purple-300 px-2 py-1 rounded">
                          {cap}
                        </span>
                      ))}
                    </div>
                  </div>
                  {selectedModule.lastSync && (
                    <div>
                      <p className="text-xs text-gray-400 uppercase tracking-wider">Last Sync</p>
                      <p className="text-sm text-gray-300">
                        {selectedModule.lastSync.toLocaleString()}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-gray-400">Select a module to view details</p>
              )}
            </div>
          </div>
        )}

        {/* Metacognition & Memory Tab */}
        {activeTab === 'metacognition' && metacogState && memoryStats && memoryPressure && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-white mb-4">Metacognition & Memory</h2>

            {/* Top row: Phase + Confidence + Self-Assessment */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="bg-white/5 rounded-lg p-5 border border-purple-500/30">
                <h4 className="text-white font-semibold mb-4">Reasoning Phase</h4>
                <PhaseIndicator phase={metacogState.currentPhase} />
              </div>
              <div className="bg-white/5 rounded-lg p-5 border border-purple-500/30">
                <h4 className="text-white font-semibold mb-4">Overall Confidence</h4>
                <ConfidenceMeter confidence={metacogState.overallConfidence} />
                {metacogState.overallConfidence < 0.5 && (
                  <p className="text-red-400 text-xs mt-2">Low confidence — consider human review</p>
                )}
              </div>
              <div className="bg-white/5 rounded-lg p-5 border border-purple-500/30">
                <h4 className="text-white font-semibold mb-3">Self-Assessment</h4>
                <p className="text-sm text-gray-300">{metacogState.selfAssessment}</p>
                {metacogState.knowledgeGaps.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs text-yellow-400 font-semibold mb-1">Knowledge Gaps:</p>
                    <ul className="space-y-1">
                      {metacogState.knowledgeGaps.map((gap, idx) => (
                        <li key={idx} className="text-xs text-yellow-300">{gap}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Memory Pressure Gauge (prominent when needs more memory) */}
            <MemoryPressureGauge pressure={memoryPressure} />

            {/* Middle row: Memory Breakdown + Uncertainties */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <MemoryTypeBreakdown stats={memoryStats} />
              <div className="bg-white/5 rounded-lg p-5 border border-purple-500/30">
                <h4 className="text-white font-semibold mb-3">Active Uncertainties</h4>
                {metacogState.uncertainties.length > 0 ? (
                  <ul className="space-y-2">
                    {metacogState.uncertainties.map((u, idx) => (
                      <li key={idx} className="text-sm text-yellow-300 bg-yellow-500/10 rounded p-2 border border-yellow-500/20">
                        {u}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-400 text-sm">No uncertainties flagged.</p>
                )}
              </div>
            </div>

            {/* Reasoning Trace History */}
            <div className="bg-white/5 rounded-lg p-5 border border-purple-500/30">
              <h4 className="text-white font-semibold mb-4">Reasoning Trace History</h4>
              {recentTraces.length > 0 ? (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {recentTraces.slice().reverse().map((trace) => (
                    <TraceCard key={trace.id} trace={trace} />
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-sm">No reasoning traces yet. Execute a task to begin metacognitive tracking.</p>
              )}
            </div>

            {/* Active Thoughts */}
            {metacogState.activeThoughts.length > 0 && (
              <div className="bg-white/5 rounded-lg p-5 border border-purple-500/30">
                <h4 className="text-white font-semibold mb-3">Active Thought Stream</h4>
                <div className="space-y-2">
                  {metacogState.activeThoughts.map((thought, idx) => (
                    <div key={idx} className="text-sm text-gray-300 bg-purple-500/10 rounded p-2 border border-purple-500/20">
                      {thought}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Network Architecture Tab */}
        {activeTab === 'architecture' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-white mb-4">Stephanie.ai Network Architecture</h2>

            {/* Architecture Diagram */}
            <div className="bg-white/5 rounded-lg p-8 border border-purple-500/30">
              <pre className="text-xs md:text-sm text-purple-300 font-mono overflow-x-auto whitespace-pre">
{`
                              ┌─────────────────────────────────────────────────────────────┐
                              │                    STEPHANIE.AI / STEPHANIE.IO              │
                              │                 AI Orchestration & Network Hub              │
                              │                                                             │
                              │  ENS: stephanie.nobleport.eth                               │
                              │  DID: did:ens:stephanie.nobleport.eth                       │
                              └─────────────────────────────────────────────────────────────┘
                                                           │
                    ┌──────────────────────────────────────┼──────────────────────────────────────┐
                    │                                      │                                      │
           ┌────────▼────────┐                   ┌─────────▼─────────┐               ┌───────────▼───────────┐
           │  MCP PROTOCOL   │                   │  NOBLEPORT.ETH    │               │  EXTERNAL SERVICES    │
           │  AI PLATFORMS   │                   │  MODULE NETWORK   │               │  & DATA FEEDS         │
           └────────┬────────┘                   └─────────┬─────────┘               └───────────┬───────────┘
                    │                                      │                                      │
    ┌───────────────┼───────────────┐      ┌───────────────┼───────────────┐       ┌──────────────┼──────────────┐
    │               │               │      │               │               │       │              │              │
┌───▼───┐      ┌────▼────┐     ┌────▼────┐ │      ┌────────▼────────┐      │  ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
│CLAUDE │      │ CHATGPT │     │  GROK   │ │      │ PORTFOLIO MGR   │      │  │ ORACLE  │    │CUSTODIAN│   │  DeFi   │
│(Anthro│      │ (OpenAI)│     │  (xAI)  │ │      │ portfolio.noble │      │  │ NETWORK │    │ BRIDGE  │   │PROTOCOLS│
│pic)   │      │         │     │         │ │      │ port.eth        │      │  │         │    │         │   │         │
└───────┘      └─────────┘     └─────────┘ │      └─────────────────┘      │  └─────────┘    └─────────┘   └─────────┘
                                           │                               │
┌───────┐      ┌─────────┐     ┌─────────┐ │      ┌─────────────────┐      │
│GEMINI │      │ LLAMA   │     │ REPLIT  │ │      │ OPERATIONS MON  │      │
│(Google│      │ (Meta)  │     │         │ │      │ operations.noble│      │
│)      │      │         │     │         │ │      │ port.eth        │      │
└───────┘      └─────────┘     └─────────┘ │      └─────────────────┘      │
                                           │                               │
┌───────┐      ┌─────────┐     ┌─────────┐ │      ┌─────────────────┐      │
│MISTRAL│      │ COHERE  │     │PERPLEXI │ │      │ COMPLIANCE ENG  │      │
│       │      │         │     │TY       │ │      │ compliance.noble│      │
│       │      │         │     │         │ │      │ port.eth        │      │
└───────┘      └─────────┘     └─────────┘ │      └─────────────────┘      │
                                           │                               │
┌───────┐      ┌─────────┐     ┌─────────┐ │      ┌─────────────────┐      │
│ GROQ  │      │DEEPSEEK │     │HUGGING  │ │      │ NBPT GOVERNANCE │      │
│       │      │         │     │FACE     │ │      │ governance.noble│      │
│       │      │         │     │         │ │      │ port.eth        │      │
└───────┘      └─────────┘     └─────────┘ │      └─────────────────┘      │
                                           │                               │
┌───────┐                                  │      ┌─────────────────┐      │
│TOGETHER                                  │      │ INVESTOR PORTAL │      │
│AI     │                                  │      │ investors.noble │      │
│       │                                  │      │ port.eth        │      │
└───────┘                                  │      └─────────────────┘      │
                                           │                               │
                                           │      ┌─────────────────┐      │
                                           │      │ AUTHORIZED PTS  │      │
                                           │      │ ap.nobleport.eth│      │
                                           │      └─────────────────┘      │
                                           │                               │
                                           │      ┌─────────────────┐      │
                                           │      │ HOLDINGS DASH   │      │
                                           │      │ holdings.noble  │      │
                                           │      │ port.eth        │      │
                                           │      └─────────────────┘      │
                                           │                               │
                                           │      ┌─────────────────┐      │
                                           │      │ BOOKKEEPER OPS  │      │
                                           │      │ bookkeeper.noble│      │
                                           │      │ port.eth        │      │
                                           │      └─────────────────┘      │
                                           │                               │
                                           │      ┌─────────────────┐      │
                                           │      │ CPA OPERATIONS  │      │
                                           │      │ cpa.nobleport.  │      │
                                           │      │ eth             │      │
                                           │      └─────────────────┘      │
                                           │                               │
                                           │      ┌─────────────────┐      │
                                           │      │ SSI IDENTITY    │      │
                                           │      │ identity.noble  │      │
                                           │      │ port.eth        │      │
                                           │      └─────────────────┘      │
                                           │                               │
                                           └───────────────────────────────┘

                              ┌─────────────────────────────────────────────────────────────┐
                              │                    ROOT IDENTITY                            │
                              │                                                             │
                              │  ENS: nobleport.eth                                         │
                              │  DID: did:ens:nobleport.eth                                 │
                              │  ETF: etf.nobleport.eth | did:ens:etf.nobleport.eth         │
                              └─────────────────────────────────────────────────────────────┘
`}
              </pre>
            </div>

            {/* MCP Protocol Description */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white/5 rounded-lg p-6 border border-purple-500/30">
                <h3 className="text-lg font-semibold text-white mb-4">MCP Protocol Integration</h3>
                <p className="text-gray-300 text-sm mb-4">
                  Stephanie.ai uses the Model Context Protocol (MCP) to establish secure, standardized
                  connections with multiple AI platforms. This enables:
                </p>
                <ul className="space-y-2 text-sm text-gray-300">
                  <li className="flex items-start gap-2">
                    <span className="text-purple-400">*</span>
                    <span>Unified interface for all AI providers</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-purple-400">*</span>
                    <span>Intelligent task routing based on capabilities</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-purple-400">*</span>
                    <span>Automatic failover and load balancing</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-purple-400">*</span>
                    <span>DID-based authentication across platforms</span>
                  </li>
                </ul>
              </div>

              <div className="bg-white/5 rounded-lg p-6 border border-purple-500/30">
                <h3 className="text-lg font-semibold text-white mb-4">NoblePort Module Network</h3>
                <p className="text-gray-300 text-sm mb-4">
                  Each NoblePort module operates as an autonomous service with its own ENS identity
                  and DID, enabling:
                </p>
                <ul className="space-y-2 text-sm text-gray-300">
                  <li className="flex items-start gap-2">
                    <span className="text-purple-400">*</span>
                    <span>Decentralized identity verification</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-purple-400">*</span>
                    <span>Verifiable inter-module communication</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-purple-400">*</span>
                    <span>Audit-ready credential chains</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-purple-400">*</span>
                    <span>AI-enhanced operations per module</span>
                  </li>
                </ul>
              </div>
            </div>

            {/* Task Routing */}
            <div className="bg-white/5 rounded-lg p-6 border border-purple-500/30">
              <h3 className="text-lg font-semibold text-white mb-4">Intelligent Task Routing</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[
                  { task: 'Code Generation', platforms: ['Claude', 'ChatGPT', 'Replit', 'DeepSeek'] },
                  { task: 'Real-Time Analysis', platforms: ['Grok', 'Perplexity', 'Groq'] },
                  { task: 'Compliance Review', platforms: ['Claude', 'Mistral'] },
                  { task: 'Document Analysis', platforms: ['Claude', 'ChatGPT', 'Gemini'] },
                  { task: 'Market Prediction', platforms: ['Grok', 'Perplexity'] },
                  { task: 'Research Synthesis', platforms: ['Perplexity', 'Gemini', 'Claude'] },
                ].map((route, idx) => (
                  <div key={idx} className="bg-black/30 rounded-lg p-4">
                    <p className="text-white font-medium mb-2">{route.task}</p>
                    <div className="flex flex-wrap gap-1">
                      {route.platforms.map((p, pidx) => (
                        <span key={pidx} className="text-xs bg-purple-500/30 text-purple-300 px-2 py-1 rounded">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-black/30 border-t border-purple-500/30 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-center md:text-left">
              <p className="text-gray-400 text-sm">
                Stephanie.ai - AI Network Hub for NoblePort.eth Ecosystem
              </p>
              <p className="text-gray-500 text-xs mt-1">
                Powered by MCP Protocol | ENS Identity | Self-Sovereign Identity (SSI)
              </p>
            </div>
            <div className="flex gap-4 text-sm">
              <a href="https://stephanie.ai" className="text-purple-400 hover:text-purple-300 transition-colors">
                stephanie.ai
              </a>
              <a href="https://stephanie.io" className="text-purple-400 hover:text-purple-300 transition-colors">
                stephanie.io
              </a>
              <a href="https://nobleport.eth" className="text-purple-400 hover:text-purple-300 transition-colors">
                nobleport.eth
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default StephanieAINetworkHub;
