import { z } from "zod";
import { SA_MOBILE_NUMBER_REGEX } from "@/constants/regex";

/** Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Section 2 (Supplier Registration) */
export const supplierInfoSchema = z.object({
  businessName: z.string().min(1, "Business name is required"),
  registrationNumber: z.string().optional(),
  ownerName: z.string().min(1, "Owner name is required"),
  phoneNumber: z.string().regex(SA_MOBILE_NUMBER_REGEX, "Enter a valid phone number"),
  email: z.string().email("Enter a valid email address"),
});
export type SupplierInfoFormValues = z.infer<typeof supplierInfoSchema>;
