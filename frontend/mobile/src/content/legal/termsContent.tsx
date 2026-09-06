/**
 * Terms of Service — shared content. Same reasoning as
 * privacyPolicyContent.tsx: ONE source of truth used by both the
 * authenticated Settings screen and the public pre-auth screen, so the
 * two can never drift into two different versions of the same
 * document.
 *
 * REWRITTEN to reflect the platform as actually built -- the previous
 * version pre-dated Supplier Users, Connections, Stock Orders, the
 * Loan Book/Order Book distinction, and commission entirely, and only
 * described the earlier, much smaller "customer records" product.
 * Mirrors TRU_Connect_Terms_of_Service.docx (the same content,
 * generated as a formal Word document) -- see this file's own
 * DOWNLOAD_URL constant for why that document isn't linked from here
 * yet.
 *
 * REVISED AGAIN (v2.1) to add real Cancellation (5) and Refunds (6)
 * sections, once cancellation itself became a real, built feature
 * rather than unscoped future work. THE ONE THING WORTH BEING
 * EXPLICIT ABOUT: item 6 states plainly that a Cash or Proof of
 * Payment refund is a matter between the Business User and Supplier
 * User directly, since that money never passes through TRU Connect's
 * own systems at all -- there's genuinely nothing for TRU Connect to
 * reverse, guarantee, or enforce for either of those two methods.
 * This is a factual description of how those payment methods already
 * work (money changes hands directly, off-platform), not a new
 * limitation introduced by adding cancellation.
 */
import React from "react";
import {
  ScrollText, BookOpen, UserCheck, Layers, Store, Package, Link2,
  Wallet, Star, Ban, Copyright, Flag, ShieldAlert, Gavel, XCircle,
  RefreshCw, Scale, Mail, CircleSlash, Banknote,
} from "lucide-react-native";
import type { InfoParagraph } from "@/features/dashboard/business/settings/components/InfoScreen";

export const TERMS_META_LINE = "Last updated 5 September 2026 · Version 2.1 (draft)";

// No real, hosted location exists yet for the formal Word/PDF version
// of this document -- see this document's own "working draft" notice.
// Left undefined on purpose (see InfoScreen's own DownloadLink type)
// so the app shows an honest "Coming soon" rather than a dead link.
export const TERMS_DOWNLOAD_URL: string | undefined = undefined;

export const TERMS_PARAGRAPHS: InfoParagraph[] = [
  {
    heading: "Draft — pending legal review",
    body: "These Terms describe how TRU Connect is intended to be used, reflecting the platform as actually built. They have not yet been reviewed by a legal professional and will be finalised, and published as a signed PDF and a permanent web page, before the platform goes live. By using TRU Connect once these Terms are finalised, you agree to them.",
    icon: (c) => <ScrollText size={16} color={c} />,
  },
  {
    heading: "1. Two roles, one platform",
    body: "TRU Connect connects Business Users (informal businesses buying stock) with Supplier Users (the suppliers who stock them). Each account is registered under exactly one role. If you both buy and sell stock, you'll need a separate account for each role.",
    icon: (c) => <Layers size={16} color={c} />,
  },
  {
    heading: "2. Your account",
    body: "You must provide accurate information when creating your account and keep your password confidential. You're responsible for activity that happens through your account, so tell us immediately if you suspect unauthorised access. Supplier Users go through a verification step before their catalogue becomes visible to Business Users.",
    icon: (c) => <UserCheck size={16} color={c} />,
  },
  {
    heading: "3. Browsing and Connections",
    body: "Business Users can generally browse a Supplier User's public catalogue without a Connection. To place a real Stock Order, a Business User must first send a Connection request to that Supplier User (or accept one), and the other party must approve it. Either party may end an active Connection at any time.",
    icon: (c) => <Link2 size={16} color={c} />,
  },
  {
    heading: "4. Placing and deciding on Stock Orders",
    body: "Once connected, a Business User may add products to a cart and submit a Stock Order. Every Stock Order is subject to the Supplier User's own approval — a decline must include a real reason. Ending a Connection does not cancel or affect a Stock Order already submitted while it was active.",
    icon: (c) => <Package size={16} color={c} />,
  },
  {
    heading: "5. Cancelling a Stock Order",
    body: "A Business User may cancel their own Stock Order, with a real reason, at any time while it is still Pending Supplier Approval. Once a Supplier User has confirmed an order, the Business User can no longer cancel it in the app — from that point, contact the Supplier User directly. A Supplier User may also cancel an order they've already confirmed, for a genuine reason such as being unable to fulfil it, and must notify the Business User. Cancelling an order, by either party, releases any stock reserved for it.",
    icon: (c) => <CircleSlash size={16} color={c} />,
  },
  {
    heading: "6. Refunds",
    body: "TRU Connect does not process payment for Cash or Proof of Payment orders — that money changes hands directly between the Business User and the Supplier User, entirely outside TRU Connect's own systems. A refund for a cancelled or disputed Cash or Proof of Payment order is a matter between those two parties directly; TRU Connect has no visibility into, and no ability to process, guarantee, or enforce, a refund for either method. Once a card / instant EFT payment method becomes available, refunds for that method will be handled through TRU Connect's own payment processor, under its own separate, clearly-disclosed policy.",
    icon: (c) => <Banknote size={16} color={c} />,
  },
  {
    heading: "7. Your Loan Book",
    body: "TRU Connect is not a lender. The Loan Book is your own private tool for tracking informal credit sales you make to your own customers, entirely outside TRU Connect's marketplace. We do not extend credit, fund these sales, or collect debts on your behalf — any credit you extend to your own customer is a private arrangement, entirely at your own risk.",
    icon: (c) => <BookOpen size={16} color={c} />,
  },
  {
    heading: "8. Your Order Book",
    body: "The Order Book is your own private tool for tracking stock you intend to purchase from suppliers, separate from a real, submitted Stock Order.",
    icon: (c) => <Store size={16} color={c} />,
  },
  {
    heading: "9. Payments and commission",
    body: "TRU Connect currently supports Cash and Proof of Payment, both paid directly to the Supplier User — we charge no commission on either. See Refunds (6) above for what that means if such an order needs to be reversed. A card / instant EFT payment method is planned; once available, a real, disclosed commission will apply to those orders only. Business Users on the Free tier are subject to real spending limits on Cash and Proof of Payment orders, shown in the app.",
    icon: (c) => <Wallet size={16} color={c} />,
  },
  {
    heading: "10. Subscription tiers",
    body: "TRU Connect offers a Free tier to every user by default. Paid tiers with additional features and higher limits are planned; where you subscribe to one, separate, clearly-disclosed billing terms will apply.",
    icon: (c) => <Star size={16} color={c} />,
  },
  {
    heading: "11. Acceptable use",
    body: "You agree not to provide false information, list counterfeit or illegal products, attempt to circumvent spending limits or Connection requirements, harass or defraud another user, or interfere with the Platform's normal operation.",
    icon: (c) => <Ban size={16} color={c} />,
  },
  {
    heading: "12. Your content",
    body: "You retain ownership of the content you upload, such as product photos and descriptions, and grant TRU Connect a licence to host and display it as needed to operate the Platform. TRU Connect's own name, logo, and platform design remain our property.",
    icon: (c) => <Copyright size={16} color={c} />,
  },
  {
    heading: "13. Reporting and disputes",
    body: "Business Users may report a Supplier User for genuine concerns directly in the app. We may review a report and take reasonable action, but every Stock Order remains a direct transaction between the Business User and the Supplier User — TRU Connect is not a party to it and is not obligated to resolve every dispute.",
    icon: (c) => <Flag size={16} color={c} />,
  },
  {
    heading: "14. What TRU Connect is not",
    body: "TRU Connect is a marketplace and connection platform. We do not buy, sell, own, warehouse, or deliver any product listed on the Platform, and do not guarantee that any listing is accurate or that any Stock Order will be fulfilled.",
    icon: (c) => <ShieldAlert size={16} color={c} />,
  },
  {
    heading: "15. Liability",
    body: "To the maximum extent permitted by law, TRU Connect is not liable for any indirect, incidental, or consequential loss arising from your use of the Platform, including losses arising from a transaction between a Business User and a Supplier User.",
    icon: (c) => <Gavel size={16} color={c} />,
  },
  {
    heading: "16. Suspension and termination",
    body: "We may suspend or terminate an account for a genuine breach of these Terms. You may stop using TRU Connect and close your own account at any time — see Help & support.",
    icon: (c) => <XCircle size={16} color={c} />,
  },
  {
    heading: "17. Changes to these Terms",
    body: 'TRU Connect may update these Terms as the Platform evolves. Material changes will be communicated in the app before they take effect. The "Last updated" date above always reflects the current version.',
    icon: (c) => <RefreshCw size={16} color={c} />,
  },
  {
    heading: "18. Governing law",
    body: "These Terms are governed by the laws of the Republic of South Africa. Any dispute will first be attempted to be resolved informally; unresolved disputes fall under the jurisdiction of the South African courts.",
    icon: (c) => <Scale size={16} color={c} />,
  },
  {
    heading: "19. Contact us",
    body: "Questions about these Terms can be sent to the contact details under Help & support.",
    icon: (c) => <Mail size={16} color={c} />,
  },
];
