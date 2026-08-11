/**
 * Privacy Policy — shared content.
 *
 * ONE source of truth, used by BOTH the authenticated Settings screen
 * (src/features/dashboard/business/settings/screens/PrivacyPolicyScreen.tsx)
 * and the public, pre-auth screen reachable from the landing page and
 * both registration forms (app/(legal)/privacy-policy.tsx). Extracted
 * here specifically so the two never drift into two different
 * versions of the same legal document.
 *
 * REAL screen with real content — but see the "Draft — pending legal
 * review" entry below. Written in plain language describing what the
 * application ACTUALLY does today, rather than boilerplate copied from
 * elsewhere that might describe practices TruConnect doesn't follow.
 * MUST be reviewed by a legal professional before public release —
 * flagged in the content itself rather than hidden.
 */
import React from "react";
import { Database, Target, Users, Clock, Lock, ScrollText, Baby, RefreshCw, Mail } from "lucide-react-native";
import type { InfoParagraph } from "@/features/dashboard/business/settings/components/InfoScreen";

export const PRIVACY_POLICY_META_LINE = "Last updated 10 August 2026 · Version 1.0 (draft)";

export const PRIVACY_POLICY_PARAGRAPHS: InfoParagraph[] = [
  {
    heading: "Draft — pending legal review",
    body: "This policy describes how TruConnect currently handles information. It has not yet been reviewed by a legal professional and will be finalised before public release. Once finalised, it will govern how TruConnect collects, uses, and protects your information.",
    icon: (c) => <ScrollText size={16} color={c} />,
  },
  {
    heading: "1. Information we collect",
    body: "Account details you provide at sign-up (name, phone number, email, password), your business or supplier profile as you complete it, and the operational records you create while using TruConnect — customers, amounts owed, orders, and payment history.",
    icon: (c) => <Database size={16} color={c} />,
  },
  {
    heading: "2. How we use it",
    body: "Solely to provide and improve the tools in TruConnect: authenticating your account, running Loan Book and Order Book, keeping your business profile, and communicating with you about your account. We do not use your information for purposes unrelated to the service.",
    icon: (c) => <Target size={16} color={c} />,
  },
  {
    heading: "3. Who can see your information",
    body: "Your business records are yours. They are not visible to other businesses or suppliers on TruConnect, and are never sold to advertisers or data brokers. A limited number of authorised TruConnect staff may access data strictly to operate, secure, and support the platform.",
    icon: (c) => <Users size={16} color={c} />,
  },
  {
    heading: "4. How long we keep it",
    body: "Your records are retained for as long as your account remains active. Items you delete are held in Trash for 7 days so you can restore them, then permanently removed. You may request full account and data deletion at any time by contacting us — see Help & support.",
    icon: (c) => <Clock size={16} color={c} />,
  },
  {
    heading: "5. Security",
    body: "Your account is protected by your password and phone verification, and data in transit is encrypted. TruConnect follows standard industry practice for securing access to production systems.",
    icon: (c) => <Lock size={16} color={c} />,
  },
  {
    heading: "6. Your rights under POPIA",
    body: "Under South Africa's Protection of Personal Information Act, you have the right to access the personal information we hold about you, request that it be corrected, object to certain processing, and request its deletion.",
    icon: (c) => <ScrollText size={16} color={c} />,
  },
  {
    heading: "7. Children's privacy",
    body: "TruConnect is a business platform intended for adults operating or supplying a business. It is not directed at, and should not be used by, children.",
    icon: (c) => <Baby size={16} color={c} />,
  },
  {
    heading: "8. Changes to this policy",
    body: 'TruConnect reserves the right to update this policy as the platform evolves. Where a change is material, we will take reasonable steps to notify you in the app before it takes effect. The "Last updated" date above always reflects the current version.',
    icon: (c) => <RefreshCw size={16} color={c} />,
  },
  {
    heading: "9. Contact us",
    body: "Questions about this policy or your information can be sent to the contact details under Help & support.",
    icon: (c) => <Mail size={16} color={c} />,
  },
];
