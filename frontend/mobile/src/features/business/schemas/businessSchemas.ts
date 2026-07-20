import { z } from "zod";
import { SA_ID_NUMBER_REGEX, SA_MOBILE_NUMBER_REGEX } from "@/constants/regex";

/**
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Section 1 (Business
 * Registration) and docs/04_DATABASE_DESIGN.txt Section 4.2 (businesses,
 * business_addresses tables).
 */
export const businessInfoSchema = z.object({
  businessName: z.string().min(1, "Business name is required"),
  tradingName: z.string().optional(),
  businessType: z.string().min(1, "Select a business type"),
  industry: z.string().min(1, "Select an industry"),
  yearsOperating: z.string().min(1, "Years operating is required"),
  addressLine: z.string().min(1, "Business address is required"),
});
export type BusinessInfoFormValues = z.infer<typeof businessInfoSchema>;

export const ownerInfoSchema = z.object({
  ownerName: z.string().min(1, "Owner name is required"),
  saIdNumber: z.string().regex(SA_ID_NUMBER_REGEX, "Enter a valid South African ID number"),
  phoneNumber: z.string().regex(SA_MOBILE_NUMBER_REGEX, "Enter a valid phone number"),
  email: z.string().email("Enter a valid email address"),
});
export type OwnerInfoFormValues = z.infer<typeof ownerInfoSchema>;

export const tradingInfoSchema = z.object({
  monthlyRevenue: z.string().min(1, "Monthly revenue is required"),
  customersPerMonth: z.string().min(1, "Customers per month is required"),
  averageTransaction: z.string().min(1, "Average transaction value is required"),
  primarySupplier: z.string().optional(),
});
export type TradingInfoFormValues = z.infer<typeof tradingInfoSchema>;
