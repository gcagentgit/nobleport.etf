import { z } from "zod";

export const AccreditationType = z.enum([
  "income",
  "net_worth",
  "professional_certification",
  "entity",
]);

export const investorIntakeSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters").max(200),
  email: z.string().email("Invalid email address"),
  phone: z
    .string()
    .max(20)
    .regex(/^[+\d\s\-()]*$/, "Invalid phone format")
    .optional()
    .or(z.literal("")),
  accreditation_type: AccreditationType,
});

export type InvestorIntakeData = z.infer<typeof investorIntakeSchema>;

export const accreditationLabels: Record<string, string> = {
  income: "Individual Income ($200K+) or Joint Income ($300K+)",
  net_worth: "Net Worth Exceeding $1M (excluding primary residence)",
  professional_certification: "Series 7, 65, or 82 license holder",
  entity: "Entity with $5M+ in assets",
};
