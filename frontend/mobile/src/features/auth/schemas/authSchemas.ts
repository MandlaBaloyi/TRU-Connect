import { z } from "zod";
import { PASSWORD_REGEX } from "@/constants/regex";

/**
 * Zod validation schemas for authentication forms.
 * Registration is intentionally minimal -- SA ID number, mobile/phone
 * number, and registration number are collected later in the Business
 * Profile Setup wizard, not at sign-up. See src/features/business/schemas
 * for those fields.
 */

export const signInSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
  rememberMe: z.boolean().optional(),
});
export type SignInFormValues = z.infer<typeof signInSchema>;

export const businessRegisterSchema = z
  .object({
    firstName: z.string().min(1, "First name is required"),
    lastName: z.string().min(1, "Last name is required"),
    businessName: z.string().optional(),
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

export const supplierRegisterSchema = z
  .object({
    businessName: z.string().optional(),
    ownerName: z.string().min(1, "Owner name is required"),
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