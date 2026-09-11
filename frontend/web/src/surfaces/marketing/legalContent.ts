/**
 * Terms of Service and Privacy Policy text for the public web pages.
 *
 * PORTED, NOT IMPORTED, from the mobile app's
 * `src/content/legal/termsContent.tsx` and `privacyPolicyContent.tsx`.
 * Those files are React Native (they pull in `lucide-react-native`) and
 * cannot be imported here. The wording below is copied verbatim so the
 * app and the site say exactly the same thing; the only things dropped
 * are the per-heading icons, which were a mobile presentation choice.
 *
 * IF THE MOBILE LEGAL TEXT CHANGES, change it here too. Same
 * hand-kept-in-sync discipline as `design-system/tokens/brand.ts` and
 * the mobile theme -- two copies is cheaper than a shared package for a
 * document that changes rarely.
 *
 * The platform's legal name is "TruConnect" (with the space), as it
 * appears in the formal documents; the brand wordmark is "TruConnect".
 * The text below keeps the legal name.
 */

export type LegalSection = {
  heading: string;
  body: string;
};

export type LegalDocument = {
  title: string;
  metaLine: string;
  /** The opening "pending legal review" notice, rendered as a callout. */
  notice: LegalSection;
  sections: LegalSection[];
};

export const TERMS: LegalDocument = {
  title: "Terms of Service",
  metaLine: "Last updated 5 September 2026 · Version 2.1 (draft)",
  notice: {
    heading: "Draft — pending legal review",
    body: "These Terms describe how TruConnect is intended to be used, reflecting the platform as actually built. They have not yet been reviewed by a legal professional and will be finalised, and published as a signed PDF and a permanent web page, before the platform goes live. By using TruConnect once these Terms are finalised, you agree to them.",
  },
  sections: [
    {
      heading: "1. Two roles, one platform",
      body: "TruConnect connects Business Users (informal businesses buying stock) with Supplier Users (the suppliers who stock them). Each account is registered under exactly one role. If you both buy and sell stock, you'll need a separate account for each role.",
    },
    {
      heading: "2. Your account",
      body: "You must provide accurate information when creating your account and keep your password confidential. You're responsible for activity that happens through your account, so tell us immediately if you suspect unauthorised access. Supplier Users go through a verification step before their catalogue becomes visible to Business Users.",
    },
    {
      heading: "3. Browsing and Connections",
      body: "Business Users can generally browse a Supplier User's public catalogue without a Connection. To place a real Stock Order, a Business User must first send a Connection request to that Supplier User (or accept one), and the other party must approve it. Either party may end an active Connection at any time.",
    },
    {
      heading: "4. Placing and deciding on Stock Orders",
      body: "Once connected, a Business User may add products to a cart and submit a Stock Order. Every Stock Order is subject to the Supplier User's own approval — a decline must include a real reason. Ending a Connection does not cancel or affect a Stock Order already submitted while it was active.",
    },
    {
      heading: "5. Cancelling a Stock Order",
      body: "A Business User may cancel their own Stock Order, with a real reason, at any time while it is still Pending Supplier Approval. Once a Supplier User has confirmed an order, the Business User can no longer cancel it in the app — from that point, contact the Supplier User directly. A Supplier User may also cancel an order they've already confirmed, for a genuine reason such as being unable to fulfil it, and must notify the Business User. Cancelling an order, by either party, releases any stock reserved for it.",
    },
    {
      heading: "6. Refunds",
      body: "TruConnect does not process payment for Cash or Proof of Payment orders — that money changes hands directly between the Business User and the Supplier User, entirely outside TruConnect's own systems. A refund for a cancelled or disputed Cash or Proof of Payment order is a matter between those two parties directly; TruConnect has no visibility into, and no ability to process, guarantee, or enforce, a refund for either method. Once a card / instant EFT payment method becomes available, refunds for that method will be handled through TruConnect's own payment processor, under its own separate, clearly-disclosed policy.",
    },
    {
      heading: "7. Your Loan Book",
      body: "TruConnect is not a lender. The Loan Book is your own private tool for tracking informal credit sales you make to your own customers, entirely outside TruConnect's marketplace. We do not extend credit, fund these sales, or collect debts on your behalf — any credit you extend to your own customer is a private arrangement, entirely at your own risk.",
    },
    {
      heading: "8. Your Order Book",
      body: "The Order Book is your own private tool for tracking stock you intend to purchase from suppliers, separate from a real, submitted Stock Order.",
    },
    {
      heading: "9. Payments and commission",
      body: "TruConnect currently supports Cash and Proof of Payment, both paid directly to the Supplier User — we charge no commission on either. See Refunds (6) above for what that means if such an order needs to be reversed. A card / instant EFT payment method is planned; once available, a real, disclosed commission will apply to those orders only. Business Users on the Free tier are subject to real spending limits on Cash and Proof of Payment orders, shown in the app.",
    },
    {
      heading: "10. Subscription tiers",
      body: "TruConnect offers a Free tier to every user by default. Paid tiers with additional features and higher limits are planned; where you subscribe to one, separate, clearly-disclosed billing terms will apply.",
    },
    {
      heading: "11. Acceptable use",
      body: "You agree not to provide false information, list counterfeit or illegal products, attempt to circumvent spending limits or Connection requirements, harass or defraud another user, or interfere with the Platform's normal operation.",
    },
    {
      heading: "12. Your content",
      body: "You retain ownership of the content you upload, such as product photos and descriptions, and grant TruConnect a licence to host and display it as needed to operate the Platform. TruConnect's own name, logo, and platform design remain our property.",
    },
    {
      heading: "13. Reporting and disputes",
      body: "Business Users may report a Supplier User for genuine concerns directly in the app. We may review a report and take reasonable action, but every Stock Order remains a direct transaction between the Business User and the Supplier User — TruConnect is not a party to it and is not obligated to resolve every dispute.",
    },
    {
      heading: "14. What TruConnect is not",
      body: "TruConnect is a marketplace and connection platform. We do not buy, sell, own, warehouse, or deliver any product listed on the Platform, and do not guarantee that any listing is accurate or that any Stock Order will be fulfilled.",
    },
    {
      heading: "15. Liability",
      body: "To the maximum extent permitted by law, TruConnect is not liable for any indirect, incidental, or consequential loss arising from your use of the Platform, including losses arising from a transaction between a Business User and a Supplier User.",
    },
    {
      heading: "16. Suspension and termination",
      body: "We may suspend or terminate an account for a genuine breach of these Terms. You may stop using TruConnect and close your own account at any time — see Help & support.",
    },
    {
      heading: "17. Changes to these Terms",
      body: 'TruConnect may update these Terms as the Platform evolves. Material changes will be communicated in the app before they take effect. The "Last updated" date above always reflects the current version.',
    },
    {
      heading: "18. Governing law",
      body: "These Terms are governed by the laws of the Republic of South Africa. Any dispute will first be attempted to be resolved informally; unresolved disputes fall under the jurisdiction of the South African courts.",
    },
    {
      heading: "19. Contact us",
      body: "Questions about these Terms can be sent to the contact details under Help & support.",
    },
  ],
};

export const PRIVACY: LegalDocument = {
  title: "Privacy Policy",
  metaLine: "Last updated 5 September 2026 · Version 2.1 (draft)",
  notice: {
    heading: "Draft — pending legal review",
    body: "This Policy describes how TruConnect currently handles information, prepared with reference to South Africa's Protection of Personal Information Act (POPIA). It has not yet been reviewed by a legal professional and will be finalised, and published as a signed PDF and a permanent web page, before the platform goes live.",
  },
  sections: [
    {
      heading: "1. Information we collect",
      body: "Account details you provide at sign-up (name, email, phone number, password, and your role), your business or supplier profile as you complete it, product listings and inventory (Supplier Users), and the records you create in your own Loan Book and Order Book (Business Users).",
    },
    {
      heading: "2. Location — general for discovery, precise for delivery",
      body: "We collect general location (such as suburb or city) shown on a Supplier User's public profile, to help Business Users discover nearby suppliers — this alone never requires a precise address. Separately, when a Business User places a Delivery order, they choose a precise delivery location themselves on a map they control, either by dropping a pin or searching for an address. That location's exact coordinates always come directly from the map, never from a third-party lookup; a background mapping service is used only to suggest address text to speed up filling in the form, and its own suggestion is never stored as-is — only the address the Business User confirms is saved, attached to that one order. A Supplier User's own precise collection address, once they set one up, is shared only with a Business User who has an active Connection with them.",
    },
    {
      heading: "3. Stock Order and transaction information",
      body: "Details of every Stock Order you place or receive — items, price, payment method, delivery method, and status — plus, for a Business User's own order, the buyer information snapshotted onto it at the moment it's submitted, so the Supplier User can fulfil it.",
    },
    {
      heading: "4. How we use it",
      body: "Solely to provide and improve TruConnect's own tools: authenticating your account, running Connections, Stock Orders, the Loan Book, and Order Book, enforcing spending limits, detecting fraud, and communicating with you about your own account.",
    },
    {
      heading: "5. Our legal basis (POPIA)",
      body: "We process your information based on consent (where given), contractual necessity (providing the Platform you signed up for), legitimate interest (such as fraud prevention, balanced against your own rights), and legal obligation where South African law requires it.",
    },
    {
      heading: "6. Who can see your information",
      body: "Contact information is shared between a Business User and a Supplier User ONLY once a real Connection is genuinely active between them — never before, and never with anyone else. Ending a Connection stops any further sharing going forward. We never sell your information to advertisers or data brokers.",
    },
    {
      heading: "7. Security",
      body: "Your password is stored encrypted, never in plain text. We keep a real, internal security log of sensitive account actions to protect you and detect misuse — this log is for our own internal security purposes and is never shared with other users. No system is perfectly secure, but we treat this as an ongoing responsibility.",
    },
    {
      heading: "8. How long we keep it",
      body: "Your records are retained for as long as your account remains active, and for a reasonable period afterward where we have a genuine legal or business reason to. Some features, like the Loan Book, let you move a record to Trash before it's permanently deleted, giving you a real chance to restore it.",
    },
    {
      heading: "9. Your rights under POPIA",
      body: "You have the right to access the personal information we hold about you, request correction, request deletion (subject to our own legal retention obligations), object to processing based on legitimate interest, withdraw consent, and lodge a complaint with the Information Regulator of South Africa.",
    },
    {
      heading: "10. Notifications",
      body: "We send real, in-app notifications about your own account activity — a new Stock Order, a decision on one you placed, a connection request. These are core to how the Platform works and can't be fully disabled while keeping your account functional. We don't sell your contact information for marketing.",
    },
    {
      heading: "11. Children's privacy",
      body: "TruConnect is a business platform intended for adults operating or supplying a business. It is not directed at, and should not be used by, anyone under 18.",
    },
    {
      heading: "12. Cross-border transfers",
      body: "Where TruConnect uses a service provider whose own infrastructure is located outside South Africa, we take reasonable steps to ensure your information continues to receive a level of protection consistent with POPIA.",
    },
    {
      heading: "13. Changes to this policy",
      body: 'TruConnect may update this Policy as the platform evolves. Material changes will be communicated in the app before they take effect. The "Last updated" date above always reflects the current version.',
    },
    {
      heading: "14. Contact us",
      body: "Questions, requests, or complaints about this Policy or your personal information can be sent to the contact details under Help & support, addressed to TruConnect's own designated Information Officer.",
    },
  ],
};
