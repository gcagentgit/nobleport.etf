const BACKEND_URL = process.env.NOBLEPORT_BACKEND_URL || "http://localhost:8400";
const INTERNAL_TOKEN = process.env.NOBLEPORT_INVESTOR_INTERNAL_TOKEN || "";

export interface IntakePayload {
  full_name: string;
  email: string;
  phone?: string;
  accreditation_type: string;
}

export interface IntakeResponse {
  id: string;
  status: string;
  message: string;
}

export async function submitIntake(data: IntakePayload): Promise<IntakeResponse> {
  const res = await fetch(`${BACKEND_URL}/api/investor/intake`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${INTERNAL_TOKEN}`,
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Server error" }));
    throw new Error(err.detail || `Intake failed: ${res.status}`);
  }

  return res.json();
}
