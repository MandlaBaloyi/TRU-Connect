import { z } from "zod";
import { PASSWORD_REGEX } from "@/constants/regex";

/**
 * Zod validation schemas for authentication forms.
 * Registration is intentionally minimal -- SA ID number, mobile/phone
 * number, and registration number are collected later, during Business
 * Profile Setup (src/features/dashboard/business/business-profile/),
 * not at sign-up.
 */

export const signInSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
  rememberMe: z.boolean().optional(),
});
export type SignInFormValues = z.infer<typeof signInSchema>;

/** Mirrors backend shared.validation.business_name exactly: 2–50 chars,
 *  at least one letter, and not a single repeated character.
 *
 *  SHARED BY BOTH ROLES, and it has to be declared above the first
 *  schema that uses it -- `const` is not hoisted, so a reference from
 *  businessRegisterSchema below its own definition would hit the
 *  temporal dead zone at module evaluation, not at call time. That is
 *  a crash on import, before any form is ever rendered. */
const businessNameField = z
  .string()
  .trim()
  .min(2, "Business name must be at least 2 characters")
  .max(50, "Business name must be 50 characters or fewer")
  .refine((v) => /[^\W\d_]/u.test(v), "Business name must contain at least one letter")
  .refine((v) => new Set(v.replace(/\s/g, "")).size > 1, "Enter a real business name");

export const businessRegisterSchema = z
  .object({
    firstName: z.string().min(1, "First name is required"),
    lastName: z.string().min(1, "Last name is required"),
    // REQUIRED NOW. It was optional, and the backend accepted it and
    // threw it away -- so a shop's profile was seeded with the owner's
    // personal name, which is what a supplier saw in Find Business.
    businessName: businessNameField,
    email: z.string().email("Enter a valid email address"),
    password: z
      .string()
      .regex(PASSWORD_REGEX, "Password must contain at least 8 characters, including an uppercase letter, lowercase letter, number, and special character."),
    confirmPassword: z.string(),
    acceptPrivacyPolicy: z.literal(true, {
      errorMap: () => ({ message: "You must accept the Privacy Policy to continue" }),
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });
export type BusinessRegisterFormValues = z.infer<typeof businessRegisterSchema>;

/** Owner name is the optional field on the supplier side -- see
 *  businessNameField above for the shared name rule. */
export const supplierRegisterSchema = z
  .object({
    businessName: businessNameField,
    ownerName: z.string().max(200).optional(),
    email: z.string().email("Enter a valid email address"),
    password: z
      .string()
      .regex(PASSWORD_REGEX, "Password must contain at least 8 characters, including an uppercase letter, lowercase letter, number, and special character."),
    confirmPassword: z.string(),
    acceptTerms: z.literal(true, {
      errorMap: () => ({ message: "You must accept the Terms to continue" }),
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });
export type SupplierRegisterFormValues = z.infer<typeof supplierRegisterSchema>;

export const otpSchema = z.object({
  code: z.string().length(6, "Enter the 6-digit code"),
});
export type OtpFormValues = z.infer<typeof otpSchema>;




export const forgotPasswordSchema = z.object({
  email: z.string().email("Enter a valid email address"),
});
export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

export const resetPasswordSchema = z
  .object({
    newPassword: z
      .string()
      .regex(
        PASSWORD_REGEX,
        "Password must be at least 8 characters, with uppercase, lowercase, a number, and a special character"
      ),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });
export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;