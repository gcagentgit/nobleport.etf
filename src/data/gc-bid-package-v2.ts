/**
 * GC Bid Package v2 — Irwin Residence, Newburyport, MA
 * Full trade scopes (bid-ready), cost ranges, markup, schedule, risk register
 * CSI division structure — hand directly to subs or lenders
 */

// ─── Types ───────────────────────────────────────────────────────────────────

export interface CostRange {
  low: number;
  high: number;
}

export interface SubScope {
  description: string;
  items: string[];
}

export interface ControlPoint {
  description: string;
  critical: boolean;
}

export interface TradeDiv {
  division: string;
  csiCode: string;
  laborRange: CostRange;
  materialRange: CostRange;
  totalRange: CostRange;
  subScope: SubScope;
  controlPoints: ControlPoint[];
}

export interface SchedulePhase {
  phase: string;
  durationWeeksLow: number;
  durationWeeksHigh: number;
  predecessors: string[];
  inspectionGate: boolean;
  floatDays: number;
}

export interface RiskItem {
  id: string;
  category: string;
  description: string;
  impact: "critical" | "high" | "medium";
  mitigation: string;
}

export interface MarkupModel {
  overheadPercent: number;
  profitPercent: number;
  contingencyPercent: number;
}

export interface GCBidPackageV2 {
  projectName: string;
  location: string;
  buildType: string;
  squareFootage: CostRange;
  stories: number;
  spec: string;
  created: string;
  version: string;
  hardCostRange: CostRange;
  sellPriceRange: CostRange;
  markup: MarkupModel;
  divisions: TradeDiv[];
  schedule: SchedulePhase[];
  risks: RiskItem[];
  executionPlaybook: string[];
}

// ─── Division 03: Concrete ──────────────────────────────────────────────────

const div03Concrete: TradeDiv = {
  division: "Concrete (Foundation + Slab)",
  csiCode: "03",
  laborRange: { low: 18000, high: 25000 },
  materialRange: { low: 20000, high: 30000 },
  totalRange: { low: 40000, high: 55000 },
  subScope: {
    description: "Full foundation scope — excavation through backfill",
    items: [
      "Excavate to frost depth (48\")",
      "Form + pour footings w/ rebar",
      "10\" foundation walls (engineered)",
      "Install anchor bolts @ 6' O.C.",
      "Waterproof + dampproof all walls",
      "Install footing drains to daylight/sump",
      "Backfill w/ gravel + fabric",
      "Slab prep (stone + vapor barrier)",
      "Pour 4\" slab (garage pitched)",
    ],
  },
  controlPoints: [
    { description: "Inspection before backfill", critical: true },
    { description: "Elevation benchmark locked before pour", critical: true },
    { description: "Rebar spacing verified per engineer", critical: false },
    { description: "Concrete PSI test (3000 min residential)", critical: false },
  ],
};

// ─── Division 06: Framing ───────────────────────────────────────────────────

const div06Framing: TradeDiv = {
  division: "Framing",
  csiCode: "06",
  laborRange: { low: 30000, high: 45000 },
  materialRange: { low: 30000, high: 50000 },
  totalRange: { low: 65000, high: 95000 },
  subScope: {
    description: "Complete structural framing — sill to ridge",
    items: [
      "Sill install + layout",
      "Floor framing (2x10 / I-joist)",
      "Wall framing (2x6 ext, 2x4 int)",
      "Headers + beams per plan",
      "Roof framing (rafters/trusses)",
      "Sheathing (walls + roof)",
      "Stairs + blocking",
      "Exterior PT framing where required",
    ],
  },
  controlPoints: [
    { description: "Window RO's verified before install", critical: true },
    { description: "Layout drives everything downstream — verify first", critical: true },
    { description: "Beam sizes confirmed against structural drawings", critical: true },
    { description: "Sheathing nailing pattern per code", critical: false },
  ],
};

// ─── Division 07: Roofing ───────────────────────────────────────────────────

const div07Roofing: TradeDiv = {
  division: "Roofing",
  csiCode: "07",
  laborRange: { low: 10000, high: 15000 },
  materialRange: { low: 12000, high: 18000 },
  totalRange: { low: 22000, high: 30000 },
  subScope: {
    description: "Complete roofing system — underlayment through gutters",
    items: [
      "Ice & water shield (MA code critical)",
      "Synthetic underlayment",
      "Architectural shingles",
      "Step + counter flashing",
      "Drip edge + ridge vent",
      "Gutters + downspouts",
    ],
  },
  controlPoints: [
    { description: "Flashing inspection before shingle close", critical: true },
    { description: "Weather window management — no open decking overnight", critical: true },
    { description: "Valley and penetration details per manufacturer spec", critical: false },
  ],
};

// ─── Division 08: Windows & Doors ───────────────────────────────────────────

const div08Openings: TradeDiv = {
  division: "Windows & Doors",
  csiCode: "08",
  laborRange: { low: 6000, high: 10000 },
  materialRange: { low: 12000, high: 20000 },
  totalRange: { low: 18000, high: 30000 },
  subScope: {
    description: "All openings — windows, ext/int doors, hardware",
    items: [
      "Install all windows per schedule",
      "Sill pans (required)",
      "Tape + liquid flashing",
      "Air seal (foam)",
      "Exterior doors install",
    ],
  },
  controlPoints: [
    { description: "Water test random openings", critical: true },
    { description: "Flashing failures = callbacks — verify before close-in", critical: true },
    { description: "Rough opening tolerances checked", critical: false },
  ],
};

// ─── Division 26: Electrical ────────────────────────────────────────────────

const div26Electrical: TradeDiv = {
  division: "Electrical (Rough)",
  csiCode: "26",
  laborRange: { low: 10000, high: 15000 },
  materialRange: { low: 8000, high: 12000 },
  totalRange: { low: 18000, high: 25000 },
  subScope: {
    description: "Full electrical rough — service through devices",
    items: [
      "Service + panel install (200A)",
      "Full rough wiring",
      "Device boxes",
      "Recessed lighting layout",
      "Smoke/CO interconnected system",
      "GFCI/AFCI compliance",
    ],
  },
  controlPoints: [
    { description: "Panel schedule reviewed before rough", critical: true },
    { description: "AFCI/GFCI per NEC 2020+ requirements", critical: true },
    { description: "Low voltage paths roughed before insulation", critical: false },
  ],
};

// ─── Division 22: Plumbing ──────────────────────────────────────────────────

const div22Plumbing: TradeDiv = {
  division: "Plumbing (Rough)",
  csiCode: "22",
  laborRange: { low: 12000, high: 18000 },
  materialRange: { low: 10000, high: 15000 },
  totalRange: { low: 22000, high: 30000 },
  subScope: {
    description: "Full plumbing rough — service through pressure test",
    items: [
      "Water supply (PEX or copper)",
      "DWV system",
      "Vent stacks through roof",
      "Tub/shower set",
      "Laundry + hose bibs",
      "Pressure test system",
    ],
  },
  controlPoints: [
    { description: "Pressure test before close-in (hold 30 min)", critical: true },
    { description: "Vent stack locations coordinated with roof plan", critical: false },
    { description: "Hot/cold orientation verified at all fixtures", critical: false },
  ],
};

// ─── Schedule ───────────────────────────────────────────────────────────────

const masterSchedule: SchedulePhase[] = [
  {
    phase: "Excavation + Foundation",
    durationWeeksLow: 2,
    durationWeeksHigh: 3,
    predecessors: [],
    inspectionGate: true,
    floatDays: 3,
  },
  {
    phase: "Framing",
    durationWeeksLow: 3,
    durationWeeksHigh: 5,
    predecessors: ["Excavation + Foundation"],
    inspectionGate: true,
    floatDays: 0,
  },
  {
    phase: "Roofing",
    durationWeeksLow: 1,
    durationWeeksHigh: 2,
    predecessors: ["Framing"],
    inspectionGate: false,
    floatDays: 2,
  },
  {
    phase: "Windows & Doors",
    durationWeeksLow: 1,
    durationWeeksHigh: 1,
    predecessors: ["Framing"],
    inspectionGate: false,
    floatDays: 3,
  },
  {
    phase: "MEP Rough-In",
    durationWeeksLow: 2,
    durationWeeksHigh: 3,
    predecessors: ["Roofing", "Windows & Doors"],
    inspectionGate: true,
    floatDays: 0,
  },
];

// ─── Risk Register ──────────────────────────────────────────────────────────

const riskRegister: RiskItem[] = [
  {
    id: "RISK-01",
    category: "Foundation",
    description: "Foundation elevation or layout errors — permanent liability, cannot be reworked",
    impact: "critical",
    mitigation: "Lock elevation benchmark before pour. Double-check layout with engineer.",
  },
  {
    id: "RISK-02",
    category: "Framing",
    description: "Framing layout mistakes cascade into windows, cabinets, and MEP conflicts",
    impact: "critical",
    mitigation: "Verify all RO's and beam pockets before sheathing. Layout drives everything.",
  },
  {
    id: "RISK-03",
    category: "Trade Coordination",
    description: "Electrician + plumber stacking in walls — conflict zone for routing",
    impact: "high",
    mitigation: "Schedule joint walk-through before rough. Assign wall territories.",
  },
  {
    id: "RISK-04",
    category: "Weather",
    description: "Weather exposure during framing — delays + material damage + mold risk",
    impact: "high",
    mitigation: "Dry-in ASAP. Tarp open framing overnight. Prioritize roof + windows.",
  },
  {
    id: "RISK-05",
    category: "Schedule",
    description: "Inspection delays from municipality — can stall entire critical path",
    impact: "medium",
    mitigation: "Schedule inspections 48–72 hrs ahead. Maintain inspector relationship.",
  },
];

// ─── Markup Model ───────────────────────────────────────────────────────────

const markup: MarkupModel = {
  overheadPercent: 15,
  profitPercent: 10,
  contingencyPercent: 5,
};

// ─── Package Assembly ───────────────────────────────────────────────────────

export const gcBidPackageV2: GCBidPackageV2 = {
  projectName: "Irwin Residence — Full GC Bid Package",
  location: "Newburyport, MA",
  buildType: "Single-family, wood frame",
  squareFootage: { low: 2600, high: 2800 },
  stories: 2,
  spec: "Mid-upper",
  created: "2026-03-17",
  version: "2.0 — Bid Ready",
  hardCostRange: { low: 260000, high: 320000 },
  sellPriceRange: { low: 325000, high: 400000 },
  markup,
  divisions: [
    div03Concrete,
    div06Framing,
    div07Roofing,
    div08Openings,
    div26Electrical,
    div22Plumbing,
  ],
  schedule: masterSchedule,
  risks: riskRegister,
  executionPlaybook: [
    "Lock foundation elevations early",
    "Frame fast but verify openings",
    "Dry-in ASAP (roof + windows)",
    "Control subs daily during rough",
    "Schedule joint MEP walk-through before rough inspection",
    "Maintain 48-hr inspection lead time with municipality",
  ],
};
