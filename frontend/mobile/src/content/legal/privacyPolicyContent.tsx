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
 * REWRITTEN, grounded in POPIA (South Africa's own Protection of
 * Personal Information Act), to reflect the platform as actually
 * built. The previous version said business records were "not visible
 * to other businesses or suppliers" -- genuinely no longer true, given
 * the real, connection-gated contact-sharing model this platform
 * actually has (see entry 3 below). Mirrors
 * TRU_Connect_Privacy_Policy.docx -- see TERMS_DOWNLOAD_URL's own
 * comment in termsContent.tsx for why the formal document isn't
 * linked from here yet.
 *
 * REVISED AGAIN (v2.1) once the real delivery map-picker shipped --
 * entry 2 previously said no precise address was ever required or
 * stored, which stopped being true the moment a Business User could
 * drop a pin for their own Delivery order. Rewritten to describe what
 * actually happens now: the pin's coordinates are the Business User's
 * own map interaction, never a geocoding provider's output; a
 * background mapping service only ever suggests address TEXT to
 * speed up the form, and that suggestion itself is never the thing
 * stored -- only what the Business User confirms is.
 */
import React from "react";
import {
  ScrollText, Database, MapPin, Package, Target, Scale, Link2, Lock,
  Clock, ShieldCheck, Bell, Baby, Globe, RefreshCw, Mail,
} from "lucide-react-native";
import type { InfoParagraph } from "@/features/dashboard/shared/settings/components/InfoScreen";

export const PRIVACY_POLICY_META_LINE = "Last updated 5 September 2026 · Version 2.1 (draft)";

export const PRIVACY_POLICY_DOWNLOAD_URL: string | undefined = undefined;

export const PRIVACY_POLICY_PARAGRAPHS: InfoParagraph[] = [
  {
    heading: "Draft — pending legal review",
    body: "This Policy describes how TRU Connect currently handles information, prepared with reference to South Africa's Protection of Personal Information Act (POPIA). It has not yet been reviewed by a legal professional and will be finalised, and published as a signed PDF and a permanent web page, before the platform goes live.",
    icon: (c) => <ScrollText size={16} color={c} />,
  },
  {
    heading: "1. Information we collect",
    body: "Account details you provide at sign-up (name, email, phone number, password, and your role), your business or supplier profile as you complete it, product listings and inventory (Supplier Users), and the records you create in your own Loan Book and Order Book (Business Users).",
    icon: (c) => <Database size={16} color={c} />,
  },
  {
    heading: "2. Location — general for discovery, precise for delivery",
    body: "We collect general location (such as suburb or city) shown on a Supplier User's public profile, to help Business Users discover nearby suppliers — this alone never requires a precise address. Separately, when a Business User places a Delivery order, they choose a precise delivery location themselves on a map they control, either by dropping a pin or searching for an address. That location's exact coordinates always come directly from the map, never from a third-party lookup; a background mapping service is used only to suggest address text to speed up filling in the form, and its own suggestion is never stored as-is — only the address the Business User confirms is saved, attached to that one order. A Supplier User's own precise collection address, once they set one up, is shared only with a Business User who has an active Connection with them.",
    icon: (c) => <MapPin size={16} color={c} />,
  },
  {
    heading: "3. Stock Order and transaction information",
    body: "Details of every Stock Order you place or receive — items, price, payment method, delivery method, and status — plus, for a Business User's own order, the buyer information snapshotted onto it at the moment it's submitted, so the Supplier User can fulfil it.",
    icon: (c) => <Package size={16} color={c} />,
  },
  {
    heading: "4. How we use it",
    body: "Solely to provide and improve TRU Connect's own tools: authenticating your account, running Connections, Stock Orders, the Loan Book, and Order Book, enforcing spending limits, detecting fraud, and communicating with you about your own account.",
    icon: (c) => <Target size={16} color={c} />,
  },
  {
    heading: "5. Our legal basis (POPIA)",
    body: "We process your information based on consent (where given), contractual necessity (providing the Platform you signed up for), legitimate interest (such as fraud prevention, balanced against your own rights), and legal obligation where South African law requires it.",
    icon: (c) => <Scale size={16} color={c} />,
  },
  {
    heading: "6. Who can see your information",
    body: "Contact information is shared between a Business User and a Supplier User ONLY once a real Connection is genuinely active between them — never before, and never with anyone else. Ending a Connection stops any further sharing going forward. We never sell your information to advertisers or data brokers.",
    icon: (c) => <Link2 size={16} color={c} />,
  },
  {
    heading: "7. Security",
    body: "Your password is stored encrypted, never in plain text. We keep a real, internal security log of sensitive account actions to protect you and detect misuse — this log is for our own internal security purposes and is never shared with other users. No system is perfectly secure, but we treat this as an ongoing responsibility.",
    icon: (c) => <Lock size={16} color={c} />,
  },
  {
    heading: "8. How long we keep it",
    body: "Your records are retained for as long as your account remains active, and for a reasonable period afterward where we have a genuine legal or business reason to. Some features, like the Loan Book, let you move a record to Trash before it's permanently deleted, giving you a real chance to restore it.",
    icon: (c) => <Clock size={16} color={c} />,
  },
  {
    heading: "9. Your rights under POPIA",
    body: "You have the right to access the personal information we hold about you, request correction, request deletion (subject to our own legal retention obligations), object to processing based on legitimate interest, withdraw consent, and lodge a complaint with the Information Regulator of South Africa.",
    icon: (c) => <ShieldCheck size={16} color={c} />,
  },
  {
    heading: "10. Notifications",
    body: "We send real, in-app notifications about your own account activity — a new Stock Order, a decision on one you placed, a connection request. These are core to how the Platform works and can't be fully disabled while keeping your account functional. We don't sell your contact information for marketing.",
    icon: (c) => <Bell size={16} color={c} />,
  },
  {
    heading: "11. Children's privacy",
    body: "TRU Connect is a business platform intended for adults operating or supplying a business. It is not directed at, and should not be used by, anyone under 18.",
    icon: (c) => <Baby size={16} color={c} />,
  },
  {
    heading: "12. Cross-border transfers",
    body: "Where TRU Connect uses a service provider whose own infrastructure is located outside South Africa, we take reasonable steps to ensure your information continues to receive a level of protection consistent with POPIA.",
    icon: (c) => <Globe size={16} color={c} />,
  },
  {
    heading: "13. Changes to this policy",
    body: 'TRU Connect may update this Policy as the platform evolves. Material changes will be communicated in the app before they take effect. The "Last updated" date above always reflects the current version.',
    icon: (c) => <RefreshCw size={16} color={c} />,
  },
  {
    heading: "14. Contact us",
    body: "Questions, requests, or complaints about this Policy or your personal information can be sent to the contact details under Help & support, addressed to TRU Connect's own designated Information Officer.",
    icon: (c) => <Mail size={16} color={c} />,
  },
];
