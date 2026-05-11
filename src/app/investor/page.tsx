"use client";

import { useActionState } from "react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { intakeAction, type IntakeResult } from "./actions";
import { accreditationLabels } from "@/lib/investorValidation";

const initialState: IntakeResult = { success: false, error: "" };

export default function InvestorIntakePage() {
  const router = useRouter();
  const [state, formAction, pending] = useActionState(
    async (_prev: IntakeResult, formData: FormData) => intakeAction(formData),
    initialState,
  );

  useEffect(() => {
    if (state.success) {
      router.push("/verification-pending");
    }
  }, [state.success, router]);

  return (
    <div className="mx-auto max-w-lg">
      <h1 className="mb-2 text-2xl font-bold">Accredited Investor Application</h1>
      <p className="mb-8 text-sm text-gray-400">
        All fields are encrypted with AES-256-GCM before storage. Your information is
        never stored in plaintext.
      </p>

      {!state.success && state.error && (
        <div className="mb-6 rounded border border-red-500/50 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {state.error}
        </div>
      )}

      <form action={formAction} className="flex flex-col gap-5">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-300">Full Legal Name</span>
          <input
            name="full_name"
            type="text"
            required
            minLength={2}
            maxLength={200}
            className="rounded border border-nb-slate bg-nb-navy px-3 py-2 text-white placeholder-gray-500 focus:border-nb-gold focus:outline-none"
            placeholder="As it appears on government ID"
          />
          {!state.success && state.fieldErrors?.full_name && (
            <span className="text-xs text-red-400">{state.fieldErrors.full_name[0]}</span>
          )}
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-300">Email Address</span>
          <input
            name="email"
            type="email"
            required
            className="rounded border border-nb-slate bg-nb-navy px-3 py-2 text-white placeholder-gray-500 focus:border-nb-gold focus:outline-none"
            placeholder="investor@example.com"
          />
          {!state.success && state.fieldErrors?.email && (
            <span className="text-xs text-red-400">{state.fieldErrors.email[0]}</span>
          )}
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-300">
            Phone <span className="text-gray-500">(optional)</span>
          </span>
          <input
            name="phone"
            type="tel"
            maxLength={20}
            className="rounded border border-nb-slate bg-nb-navy px-3 py-2 text-white placeholder-gray-500 focus:border-nb-gold focus:outline-none"
            placeholder="+1 (978) 555-0100"
          />
        </label>

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1 text-sm font-medium text-gray-300">
            Accreditation Basis
          </legend>
          {Object.entries(accreditationLabels).map(([value, label]) => (
            <label key={value} className="flex items-start gap-3 rounded border border-nb-slate p-3 hover:border-nb-gold/50">
              <input
                type="radio"
                name="accreditation_type"
                value={value}
                required
                className="mt-0.5 accent-nb-gold"
              />
              <span className="text-sm text-gray-300">{label}</span>
            </label>
          ))}
          {!state.success && state.fieldErrors?.accreditation_type && (
            <span className="text-xs text-red-400">{state.fieldErrors.accreditation_type[0]}</span>
          )}
        </fieldset>

        <button
          type="submit"
          disabled={pending}
          className="mt-2 rounded-lg bg-nb-gold px-6 py-3 font-semibold text-nb-navy transition hover:brightness-110 disabled:opacity-50"
        >
          {pending ? "Submitting…" : "Submit Application"}
        </button>

        <p className="text-xs text-gray-500">
          By submitting, you represent that the information provided is true and accurate.
          Verification of accredited investor status is required under SEC Rule 506(c)
          prior to any investment.
        </p>
      </form>
    </div>
  );
}
