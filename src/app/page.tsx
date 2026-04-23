'use client';

import { useState, FormEvent } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const PROJECT_TYPES = [
  'Residential Renovation',
  'Commercial Build-Out',
  'New Construction',
  'Historic Restoration',
  'Permitting Only',
  'Other',
];

interface IntakeResult {
  lead_id: string;
  status: string;
}

interface ProposalResult {
  proposal_id: string;
  estimated_total: number;
  deposit_amount: number;
  deposit_pct: number;
}

export default function IntakePage() {
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    property_address: '',
    project_type: '',
    description: '',
    estimated_budget: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{
    lead: IntakeResult;
    proposal: ProposalResult;
  } | null>(null);
  const [error, setError] = useState('');

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const intakeRes = await fetch(`${API_URL}/api/intake`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          estimated_budget: form.estimated_budget
            ? parseFloat(form.estimated_budget)
            : undefined,
        }),
      });

      if (!intakeRes.ok) {
        const body = await intakeRes.json();
        throw new Error(body.error ?? 'Intake submission failed');
      }

      const lead: IntakeResult = await intakeRes.json();

      const proposalRes = await fetch(`${API_URL}/api/proposals/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lead_id: lead.lead_id }),
      });

      if (!proposalRes.ok) {
        const body = await proposalRes.json();
        throw new Error(body.error ?? 'Proposal generation failed');
      }

      const proposal: ProposalResult = await proposalRes.json();
      setResult({ lead, proposal });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setSubmitting(false);
    }
  }

  if (result) {
    return (
      <main style={styles.container}>
        <div style={styles.card}>
          <h1 style={styles.heading}>Proposal Ready</h1>
          <div style={styles.successBox}>
            <p><strong>Lead ID:</strong> {result.lead.lead_id}</p>
            <p><strong>Proposal ID:</strong> {result.proposal.proposal_id}</p>
            <p><strong>Estimated Total:</strong> ${result.proposal.estimated_total.toLocaleString()}</p>
            <p><strong>Deposit ({(result.proposal.deposit_pct * 100).toFixed(0)}%):</strong> ${result.proposal.deposit_amount.toLocaleString()}</p>
          </div>
          <button
            style={styles.button}
            onClick={() => { setResult(null); setForm({ name: '', email: '', phone: '', property_address: '', project_type: '', description: '', estimated_budget: '' }); }}
          >
            Submit Another
          </button>
        </div>
      </main>
    );
  }

  return (
    <main style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.heading}>NoblePort Project Intake</h1>
        <p style={styles.subheading}>Tell us about your project to receive a proposal and deposit link.</p>

        {error && <div style={styles.errorBox}>{error}</div>}

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            Full Name *
            <input
              style={styles.input}
              value={form.name}
              onChange={(e) => update('name', e.target.value)}
              required
            />
          </label>

          <label style={styles.label}>
            Email *
            <input
              style={styles.input}
              type="email"
              value={form.email}
              onChange={(e) => update('email', e.target.value)}
              required
            />
          </label>

          <label style={styles.label}>
            Phone
            <input
              style={styles.input}
              type="tel"
              value={form.phone}
              onChange={(e) => update('phone', e.target.value)}
            />
          </label>

          <label style={styles.label}>
            Property Address *
            <input
              style={styles.input}
              value={form.property_address}
              onChange={(e) => update('property_address', e.target.value)}
              required
            />
          </label>

          <label style={styles.label}>
            Project Type *
            <select
              style={styles.input}
              value={form.project_type}
              onChange={(e) => update('project_type', e.target.value)}
              required
            >
              <option value="">Select a project type</option>
              {PROJECT_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </label>

          <label style={styles.label}>
            Description
            <textarea
              style={{ ...styles.input, minHeight: 80, resize: 'vertical' as const }}
              value={form.description}
              onChange={(e) => update('description', e.target.value)}
            />
          </label>

          <label style={styles.label}>
            Estimated Budget ($)
            <input
              style={styles.input}
              type="number"
              min="0"
              step="100"
              value={form.estimated_budget}
              onChange={(e) => update('estimated_budget', e.target.value)}
              placeholder="e.g. 50000"
            />
          </label>

          <button type="submit" style={styles.button} disabled={submitting}>
            {submitting ? 'Submitting...' : 'Submit & Get Proposal'}
          </button>
        </form>
      </div>
    </main>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  card: {
    background: '#fff',
    borderRadius: 12,
    boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
    padding: 40,
    maxWidth: 520,
    width: '100%',
  },
  heading: {
    fontSize: 24,
    fontWeight: 700,
    margin: '0 0 4px',
    color: '#111',
  },
  subheading: {
    fontSize: 14,
    color: '#666',
    margin: '0 0 24px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
  },
  label: {
    display: 'flex',
    flexDirection: 'column',
    fontSize: 13,
    fontWeight: 600,
    color: '#333',
    gap: 4,
  },
  input: {
    padding: '10px 12px',
    borderRadius: 6,
    border: '1px solid #ddd',
    fontSize: 14,
    fontFamily: 'inherit',
    outline: 'none',
  },
  button: {
    padding: '12px 20px',
    borderRadius: 8,
    border: 'none',
    background: '#1a73e8',
    color: '#fff',
    fontSize: 15,
    fontWeight: 600,
    cursor: 'pointer',
    marginTop: 8,
  },
  errorBox: {
    background: '#fef2f2',
    color: '#b91c1c',
    border: '1px solid #fecaca',
    borderRadius: 8,
    padding: '10px 14px',
    fontSize: 13,
    marginBottom: 12,
  },
  successBox: {
    background: '#f0fdf4',
    border: '1px solid #bbf7d0',
    borderRadius: 8,
    padding: '16px 20px',
    fontSize: 14,
    lineHeight: 1.8,
    marginBottom: 20,
  },
};
