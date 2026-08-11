/**
 * Terms of Service — shared content. Same reasoning as
 * privacyPolicyContent.tsx: ONE source of truth used by both the
 * authenticated Settings screen and the public pre-auth screen, so the
 * two can never drift into two different versions of the same
 * document.
 */
import React from "react";
import { ScrollText, UserCheck, FileStack, ShieldAlert, Ban, CreditCard, XCircle, Gavel, RefreshCw, Mail } from "lucide-react-native";
import type { InfoParagraph } from "@/features/dashboard/business/settings/components/InfoScreen";

export const TERMS_META_LINE = "Last updated 10 August 2026 · Version 1.0 (draft)";

export const TERMS_PARAGRAPHS: InfoParagraph[] = [
  {
    heading: "Draft — pending legal review",
    body: "These terms describe how TruConnect is intended to be used. They have not yet been reviewed by a legal professional and will be finalised before public release. By using TruConnect once these terms are finalised, you agree to them.",
    icon: (c) => <ScrollText size={16} color={c} />,
  },
  {
    heading: "1. Your account",
    body: "You must provide accurate information when creating your account and keep your password confidential. You're responsible for activity that happens through your account, so tell us immediately if you suspect unauthorised access.",
    icon: (c) => <UserCheck size={16} color={c} />,
  },
  {
    heading: "2. Your business records",
    body: "The customer, order, and business records you create belong to you. You're responsible for the accuracy of what you enter and for how you handle the customer information you record, including complying with applicable data protection law yourself.",
    icon: (c) => <FileStack size={16} color={c} />,
  },
  {
    heading: "3. Acceptable use",
    body: "TruConnect may only be used for legitimate business purposes. You agree not to use it to store unlawful content, attempt to access another business's records, or interfere with the platform's normal operation.",
    icon: (c) => <ShieldAlert size={16} color={c} />,
  },
  {
    heading: "4. What TruConnect is not",
    body: "TruConnect records what your customers owe you and what orders they've placed. It is not a bank, a lender, a payment processor, or a source of financial or legal advice, and does not guarantee that any amount recorded will be recovered.",
    icon: (c) => <Ban size={16} color={c} />,
  },
  {
    heading: "5. Fees",
    body: "TruConnect's core business tools are currently provided free of charge. Should this change, you will be notified in advance of any fees before they apply to your account.",
    icon: (c) => <CreditCard size={16} color={c} />,
  },
  {
    heading: "6. Suspension and termination",
    body: "We may suspend or terminate an account that violates these terms or is used unlawfully. You may stop using TruConnect and request account deletion at any time — see Help & support.",
    icon: (c) => <XCircle size={16} color={c} />,
  },
  {
    heading: "7. Availability",
    body: "TruConnect works offline for recording business activity, but syncing and some features require a connection. The service may occasionally be unavailable for scheduled maintenance or due to circumstances beyond our control.",
    icon: (c) => <ShieldAlert size={16} color={c} />,
  },
  {
    heading: "8. Governing law",
    body: "These terms are governed by the laws of the Republic of South Africa, and any dispute will be subject to the jurisdiction of the South African courts.",
    icon: (c) => <Gavel size={16} color={c} />,
  },
  {
    heading: "9. Changes to these terms",
    body: 'TruConnect reserves the right to update these terms as the platform evolves. Where a change is material, we will take reasonable steps to notify you in the app before it takes effect. The "Last updated" date above always reflects the current version.',
    icon: (c) => <RefreshCw size={16} color={c} />,
  },
  {
    heading: "10. Contact us",
    body: "Questions about these terms can be sent to the contact details under Help & support.",
    icon: (c) => <Mail size={16} color={c} />,
  },
];
