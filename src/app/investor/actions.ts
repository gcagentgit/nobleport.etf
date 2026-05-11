"use server";

import { investorIntakeSchema } from "@/lib/investorValidation";
import { submitIntake } from "@/lib/investorApi";

export type IntakeResult =
  | { success: true; id: string; message: string }
  | { success: false; error: string; fieldErrors?: Record<string, string[]> };

export async function intakeAction(formData: FormData): Promise<IntakeResult> {
  const raw = {
    full_name: formData.get("full_name"),
    email: formData.get("email"),
    phone: formData.get("phone") || undefined,
    accreditation_type: formData.get("accreditation_type"),
  };

  const parsed = investorIntakeSchema.safeParse(raw);
  if (!parsed.success) {
    return {
      success: false,
      error: "Validation failed",
      fieldErrors: parsed.error.flatten().fieldErrors as Record<string, string[]>,
    };
  }

  try {
    const res = await submitIntake({
      full_name: parsed.data.full_name,
      email: parsed.data.email,
      phone: parsed.data.phone || undefined,
      accreditation_type: parsed.data.accreditation_type,
    });
    return { success: true, id: res.id, message: res.message };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Submission failed";
    return { success: false, error: message };
  }
}
