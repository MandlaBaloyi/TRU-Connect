import React from "react";
import { BookOpen, Wallet, ClipboardList, Store, Trash2 } from "lucide-react-native";
import { InfoScreen } from "@/features/dashboard/shared/settings/components/InfoScreen";
import { SUPPORT_CONTACTS } from "@/features/dashboard/shared/settings/supportContacts";

/**
 * REAL contact methods + real static guidance — business side.
 *
 * ROLE-SPECIFIC ON PURPOSE. This lived in shared/settings/ briefly
 * while Settings was being split, and that was wrong: every paragraph
 * below names something only a business has (Loan Book, Order Book,
 * Trash, "My Business under More"). A supplier opening the shared
 * version was being told to visit menu rows that do not exist for
 * them, which is exactly the kind of dishonest surface the rest of
 * this Settings tree is written to avoid.
 *
 * The contacts are still shared — same support team either way — and
 * live in shared/settings/supportContacts.tsx so the phone number has
 * one home. See supplier/settings/screens/HelpScreen.tsx for the other
 * half.
 */
export default function HelpScreen() {
  return (
    <InfoScreen
      contacts={SUPPORT_CONTACTS}
      paragraphs={[
        {
          heading: "Getting started",
          body: "Loan Book records what customers owe you and tracks repayments. Order Book records orders customers place with you, from pending through to complete. Both live under the Account tab.",
          icon: (c) => <BookOpen size={16} color={c} />,
        },
        {
          heading: "Loan Book basics",
          body: "Add a customer, record what they owe, and log payments as they come in. TruConnect tracks the outstanding balance automatically and flags overdue amounts so nothing slips through.",
          icon: (c) => <Wallet size={16} color={c} />,
        },
        {
          heading: "Order Book basics",
          body: "Create an order, move it through its stages as work progresses, and mark it complete once it's fulfilled. Your daily revenue and order history are tracked automatically as you go.",
          icon: (c) => <ClipboardList size={16} color={c} />,
        },
        {
          heading: "Your business profile",
          body: "My Business, under More, is where you set your business name, category, location, trading details, and how customers can reach you. Keeping this current helps the rest of TruConnect work well for you.",
          icon: (c) => <Store size={16} color={c} />,
        },
        {
          heading: "Deleted something by mistake?",
          body: "Deleted customers, entries and orders go to Trash for 7 days, where you can restore them with one tap. Trash is inside both Loan Book and Order Book.",
          icon: (c) => <Trash2 size={16} color={c} />,
        },
      ]}
    />
  );
}
