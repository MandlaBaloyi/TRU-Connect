import React from "react";
import { Phone, Mail, MessageCircle } from "lucide-react-native";

/**
 * The ONE support contact list, shared by both roles.
 *
 * Split out when Settings was made role-aware. The Help screen used to
 * be a single shared file, but almost all of its guidance turned out to
 * be business-only — Loan Book, Order Book, Trash, "My Business under
 * More" — none of which a supplier has. A supplier reading that screen
 * was being pointed at menu rows that do not exist for them.
 *
 * So the GUIDANCE is now role-specific (business/settings/screens/
 * HelpScreen.tsx and supplier/settings/screens/HelpScreen.tsx) and the
 * CONTACTS — the part that is genuinely identical, because it is the
 * same support team either way — live here so there is still only one
 * place to change the phone number.
 *
 * PLACEHOLDER VALUES -- replace phone/WhatsApp/email with the real
 * details before release. Formats matter for the Linking calls:
 *   phone: "tel:+27XXXXXXXXX"              (no spaces, country code, no leading 0)
 *   whatsapp: "https://wa.me/27XXXXXXXXX"  (same number format, no "+")
 *   email: "mailto:support@yourdomain.co.za"
 */
export const SUPPORT_CONTACTS = [
  {
    label: "Call us",
    value: "+27 00 000 0000",
    url: "tel:+27000000000",
    icon: (c: string) => <Phone size={20} color={c} />,
  },
  {
    label: "WhatsApp",
    value: "+27 00 000 0000",
    url: "https://wa.me/27000000000",
    icon: (c: string) => <MessageCircle size={20} color={c} />,
  },
  {
    label: "Email",
    value: "support@truconnect.co.za",
    url: "mailto:support@truconnect.co.za",
    icon: (c: string) => <Mail size={20} color={c} />,
  },
];
