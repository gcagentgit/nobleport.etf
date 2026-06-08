/**
 * NoblePort Construction LLC — Roofing Proposals & Estimating
 *
 * Structured proposal/estimate records for the roofing division. Powers the
 * /dashboard/roofing/proposals view. Line-item pricing is computed from field
 * measurements using transparent unit rates (see RATES) so the placeholder
 * amounts in the source proposal resolve to defensible figures pending a final
 * site verification.
 *
 * Internal estimating asset — figures are estimates, not a firm bid, until the
 * deck is inspected and the proposal is signed. Pricing reflects 2026 coastal
 * Essex County, MA labor + material costs.
 */

export type ProposalStatus = 'draft' | 'sent' | 'accepted' | 'declined';

export interface ScopeItem {
  task: string;
  included: boolean;
}

export interface LineItem {
  description: string;
  detail: string;
  qty: number; // SF, or 1 for flat fees
  unit: string; // 'SF' | 'LS'
  rate: number; // $ per unit
  amount: number; // computed
}

export interface MaterialSpec {
  component: string;
  product: string;
}

export interface PaymentMilestone {
  milestone: string;
  pct: number;
  amount: number;
  gate: string;
}

export interface RoofingProposal {
  id: string;
  proposalNo: string;
  status: ProposalStatus;
  date: string;
  preparedBy: string;
  company: string;
  projectAddress: string;
  summary?: string;

  // Overview / measurements
  totalAreaSf: number;
  pitchedAreaSf: number;
  flatAreaSf: number;
  pitch: string;
  squares: number;

  scope: ScopeItem[];
  materials: MaterialSpec[];
  lineItems: LineItem[];

  subtotal: number;
  contingencyPct: number;
  contingencyAmount: number;
  total: number;
  investmentLow: number;
  investmentHigh: number;

  durationDays: string;
  paymentSchedule: PaymentMilestone[];

  fallProtectionNote: string;
  assumptions: string[];
  exclusions: string[];
}

/** Transparent unit rates used to resolve the proposal's placeholder pricing. */
const RATES = {
  /** Pitched architectural-shingle system, $/SF: tear-off labor, ice & water,
   *  synthetic underlayment, architectural shingles, flashing, drip edge, ridge
   *  vent, plus a steep-pitch (7/12) labor factor. */
  pitchedSystemPerSf: 8.5,
  /** Flat EPDM system, $/SF: membrane, adhesive, insulation board, edge metal.
   *  Small flat sections carry a higher unit cost. */
  flatSystemPerSf: 9.5,
  /** Disposal — dumpster + haul-off, flat fee (per source proposal). */
  disposalLumpSum: 1850,
  /** Contingency for concealed deck repair found at tear-off. */
  contingencyPct: 0.1,
};

const round = (n: number) => Math.round(n);

function buildProposal(): RoofingProposal {
  const pitchedAreaSf = 940;
  const flatAreaSf = 506;
  const totalAreaSf = 1445;

  const pitchedAmount = round(pitchedAreaSf * RATES.pitchedSystemPerSf); // 7,990
  const flatAmount = round(flatAreaSf * RATES.flatSystemPerSf); // 4,807
  const disposalAmount = RATES.disposalLumpSum; // 1,850

  const lineItems: LineItem[] = [
    {
      description: 'Roofing System (Labor + Materials)',
      detail:
        'Tear-off, ice & water shield, synthetic underlayment, architectural shingles, flashing, drip edge & ridge vent (incl. 7/12 steep-pitch labor)',
      qty: pitchedAreaSf,
      unit: 'SF',
      rate: RATES.pitchedSystemPerSf,
      amount: pitchedAmount,
    },
    {
      description: 'Flat Roof Section',
      detail: 'EPDM (or equivalent) membrane system — fully adhered, insulation & edge metal',
      qty: flatAreaSf,
      unit: 'SF',
      rate: RATES.flatSystemPerSf,
      amount: flatAmount,
    },
    {
      description: 'Disposal (Dumpster & Haul-Off)',
      detail: 'Container, tipping fees & site haul-off',
      qty: 1,
      unit: 'LS',
      rate: disposalAmount,
      amount: disposalAmount,
    },
  ];

  const subtotal = pitchedAmount + flatAmount + disposalAmount; // 14,647
  const contingencyAmount = round(subtotal * RATES.contingencyPct);
  const total = subtotal;
  const investmentLow = round(subtotal / 50) * 50; // nearest $50
  const investmentHigh = round((subtotal + contingencyAmount) / 50) * 50;

  const paymentSchedule: PaymentMilestone[] = [
    { milestone: 'Deposit', pct: 0.3, amount: round(total * 0.3), gate: 'Required to schedule — no deposit, no schedule' },
    { milestone: 'Dry-in', pct: 0.4, amount: round(total * 0.4), gate: 'Tear-off + underlayment / ice & water complete' },
    { milestone: 'Completion', pct: 0.3, amount: total - round(total * 0.3) - round(total * 0.4), gate: 'Final inspection & closeout sign-off' },
  ];

  return {
    id: '20-61st-street-newburyport',
    proposalNo: 'NP-RF-2026-0042',
    status: 'draft',
    date: 'June 8, 2026',
    preparedBy: 'NoblePort Construction LLC — Estimating',
    company: 'NoblePort Construction LLC',
    projectAddress: '20 61st Street, Newburyport, MA 01950',

    totalAreaSf,
    pitchedAreaSf,
    flatAreaSf,
    pitch: '7/12',
    squares: Math.round((totalAreaSf / 100) * 10) / 10,

    scope: [
      { task: 'Remove existing roofing materials', included: true },
      { task: 'Install ice & water shield and synthetic underlayment', included: true },
      { task: 'Install architectural shingles', included: true },
      { task: 'Install flat roofing system (EPDM or equivalent)', included: true },
      { task: 'Install flashing, drip edge, and ventilation', included: true },
      { task: 'Complete site cleanup', included: true },
    ],

    materials: [
      { component: 'Eaves / valley underlayment', product: 'Self-adhering ice & water shield' },
      { component: 'Field underlayment', product: 'Synthetic underlayment (full coverage)' },
      { component: 'Pitched roof', product: 'Architectural (dimensional) asphalt shingles' },
      { component: 'Flat roof', product: 'EPDM membrane, fully adhered (or equivalent)' },
      { component: 'Flashing & edge', product: 'Aluminum step/counter flashing + drip edge' },
      { component: 'Ventilation', product: 'Continuous ridge vent' },
    ],

    lineItems,
    subtotal,
    contingencyPct: RATES.contingencyPct,
    contingencyAmount,
    total,
    investmentLow,
    investmentHigh,

    durationDays: '2–4 days (weather permitting)',
    paymentSchedule,

    fallProtectionNote:
      'At a 7/12 pitch the pitched section exceeds the low-slope threshold and requires personal fall arrest (PFAS) under the NoblePort Fall Protection Program. Anchorage, harness inspection, and supervisor approval gates must clear before WORK_AUTHORIZED is emitted for this job.',

    assumptions: [
      'Pricing assumes a single existing roofing layer; each additional layer is billed per square at tear-off.',
      'Includes a 10% concealed-deck-repair contingency; sheathing replacement beyond the allowance is billed at unit rate.',
      'Figures are an estimate pending on-site deck inspection and final material selection; not a firm bid until signed.',
      'Schedule of 2–4 days is weather-permitting and assumes normal site access for a dumpster.',
    ],
    exclusions: [
      'Building permit fees (owner-provided or billed at cost).',
      'Structural framing repairs or rafter/truss work.',
      'Skylight, chimney masonry, or solar reinstallation unless separately quoted.',
      'Interior repairs from pre-existing leaks.',
    ],
  };
}

export const proposal20_61st: RoofingProposal = buildProposal();

/**
 * 3 Otis Place — partial "half-roof" re-roof of one lower slope, priced per
 * square ($950/square = $9.50/SF) per owner scope. Measurements from the Roofr
 * report (Nearmap imagery Mar 31, 2023): full roof 1,979 SF / 1,895 SF pitched /
 * 22 facets / predominant pitch 10/12. The two main 10/12 lower slopes measure
 * 707 + 717 SF (≈ the 1,422 SF predominant-pitch area); this proposal covers
 * one of them.
 */
function buildOtisProposal(): RoofingProposal {
  const slopeAreaSf = 717; // one lower slope (the larger of the two main 10/12 facets)
  const squares = Math.round((slopeAreaSf / 100) * 100) / 100; // 7.17 squares
  const pricePerSquare = 950; // owner-quoted: $950 / square (100 SF) = $9.50/SF
  const roofingAmount = round(slopeAreaSf * (pricePerSquare / 100)); // 6,812
  const chimneyAllowance = 650; // re-flash; masonry/crown excluded
  const skylightAllowance = 350; // re-flash existing skylight in place

  const lineItems: LineItem[] = [
    {
      description: 'Partial Re-Roof — One Lower Slope',
      detail:
        'Tear-off, ice & water shield, synthetic underlayment, architectural shingles & drip edge (disposal of removed slope included)',
      qty: squares,
      unit: 'SQ',
      rate: pricePerSquare,
      amount: roofingAmount,
    },
    {
      description: 'Chimney Work',
      detail: 'Re-flash chimney — step & counter-flashing (masonry rebuild / crown excluded)',
      qty: 1,
      unit: 'LS',
      rate: chimneyAllowance,
      amount: chimneyAllowance,
    },
    {
      description: 'Skylight Re-Flash',
      detail: 'Re-flash existing skylight in place (glazing / unit replacement excluded)',
      qty: 1,
      unit: 'LS',
      rate: skylightAllowance,
      amount: skylightAllowance,
    },
  ];

  const subtotal = roofingAmount + chimneyAllowance + skylightAllowance; // 7,812
  const contingencyPct = 0.1;
  const contingencyAmount = round(subtotal * contingencyPct);
  const total = subtotal;
  const investmentLow = round(subtotal / 50) * 50;
  const investmentHigh = round((subtotal + contingencyAmount) / 50) * 50;

  const paymentSchedule: PaymentMilestone[] = [
    { milestone: 'Deposit', pct: 0.3, amount: round(total * 0.3), gate: 'Required to schedule — no deposit, no schedule' },
    { milestone: 'Dry-in', pct: 0.4, amount: round(total * 0.4), gate: 'Tear-off + ice & water / underlayment complete on the slope' },
    { milestone: 'Completion', pct: 0.3, amount: total - round(total * 0.3) - round(total * 0.4), gate: 'Skylight & chimney flashing done · final inspection' },
  ];

  return {
    id: '3-otis-place-newburyport',
    proposalNo: 'NP-RF-2026-0043',
    status: 'draft',
    date: 'June 8, 2026',
    preparedBy: 'NoblePort Construction LLC — Estimating',
    company: 'NoblePort Construction LLC',
    projectAddress: '3 Otis Place, Newburyport, MA 01950',
    summary:
      'Partial "half-roof" re-roof of one lower slope (~717 SF / 7.17 squares) at $950/square — tear-off, ice & water shield, synthetic underlayment, architectural shingles and drip edge, plus skylight re-flash and chimney flashing. One side only, per owner scope.',

    totalAreaSf: slopeAreaSf,
    pitchedAreaSf: slopeAreaSf,
    flatAreaSf: 0,
    pitch: '10/12',
    squares,

    scope: [
      { task: 'Remove (tear off) existing roofing — one lower slope', included: true },
      { task: 'Install ice & water shield', included: true },
      { task: 'Install synthetic underlayment', included: true },
      { task: 'Install architectural shingles', included: true },
      { task: 'Install drip edge', included: true },
      { task: 'Re-flash existing skylight', included: true },
      { task: 'Chimney flashing / counter-flashing', included: true },
      { task: 'Site cleanup & disposal', included: true },
    ],

    materials: [
      { component: 'Eaves / penetration underlayment', product: 'Self-adhering ice & water shield' },
      { component: 'Field underlayment', product: 'Synthetic underlayment (full coverage)' },
      { component: 'Roofing', product: 'Architectural (dimensional) asphalt shingles' },
      { component: 'Edge', product: '10" aluminum drip edge (eaves + rakes)' },
      { component: 'Chimney', product: 'Aluminum step + counter-flashing' },
      { component: 'Skylight', product: 'Manufacturer step-flashing / re-flash kit' },
    ],

    lineItems,
    subtotal,
    contingencyPct,
    contingencyAmount,
    total,
    investmentLow,
    investmentHigh,

    durationDays: '1–2 days (weather permitting)',
    paymentSchedule,

    fallProtectionNote:
      'At a 10/12 (steep-slope) pitch this slope requires personal fall arrest (PFAS) and likely roof brackets/jacks under the NoblePort Fall Protection Program. Anchorage, harness inspection, and supervisor approval gates must clear before WORK_AUTHORIZED is emitted for this job.',

    assumptions: [
      'Full roof per Roofr report (Nearmap Mar 31, 2023): 1,979 SF total, 1,895 SF pitched, 22 facets, predominant pitch 10/12. This proposal covers ONE lower slope only (~717 SF / 7.17 squares).',
      '$950 per square is an installed price covering tear-off, ice & water shield, synthetic underlayment, architectural shingles and drip edge; disposal of the removed slope is included.',
      'Chimney work is a flashing / counter-flashing allowance; masonry rebuild, crown or cap repair is excluded unless separately quoted.',
      'Skylight is re-flashed in place; skylight glazing or unit replacement is excluded.',
      'Includes a 10% concealed-deck-repair contingency; sheathing replacement beyond the allowance is billed at unit rate.',
      'Figures are an estimate pending on-site deck inspection; not a firm bid until signed.',
    ],
    exclusions: [
      'Opposite slope, upper roof sections, and flat/low-slope areas (not in this scope).',
      'Chimney masonry, crown, or cap work.',
      'Skylight glazing or unit replacement.',
      'Building permit fees (owner-provided or billed at cost).',
      'Structural framing / rafter / decking replacement beyond the contingency allowance.',
    ],
  };
}

export const proposal3Otis: RoofingProposal = buildOtisProposal();

export const roofingProposals: RoofingProposal[] = [proposal20_61st, proposal3Otis];

export function getProposalById(id: string): RoofingProposal | undefined {
  return roofingProposals.find((p) => p.id === id);
}
