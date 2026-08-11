import React from "react";
import { Phone, Mail, MessageCircle, BookOpen, Wallet, ClipboardList, Store, Trash2 } from "lucide-react-native";
import { InfoScreen } from "@/features/dashboard/business/settings/components/InfoScreen";

/**
 * REAL contact methods + real static guidance.
 *
 * PLACEHOLDER VALUES BELOW -- replace phone/WhatsApp/email with your
 * real details before release. Formats matter for the Linking calls:
 *   phone: "tel:+27XXXXXXXXX"          (no spaces, country code, no leading 0)
 *   whatsapp: "https://wa.me/27XXXXXXXXX"  (same number format, no "+")
 *   email: "mailto:support@yourdomain.co.za"
 */
export default function HelpScreen() {
  return (
    <InfoScreen
      contacts={[
        {
          label: "Call us",
          value: "+27 00 000 0000",
          url: "tel:+27000000000",
          icon: (c) => <Phone size={20} color={c} />,
        },
        {
          label: "WhatsApp",
          value: "+27 00 000 0000",
          url: "https://wa.me/27000000000",
          icon: (c) => <MessageCircle size={20} color={c} />,
        },
        {
          label: "Email",
          value: "support@truconnect.co.za",
          url: "mailto:support@truconnect.co.za",
          icon: (c) => <Mail size={20} color={c} />,
        },
      ]}
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
