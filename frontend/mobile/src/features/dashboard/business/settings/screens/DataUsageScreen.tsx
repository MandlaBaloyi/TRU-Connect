import React from "react";
import { Database, ShieldCheck, Users, Lock, Ban, Trash2 } from "lucide-react-native";
import { InfoScreen } from "@/features/dashboard/business/settings/components/InfoScreen";

/** REAL static information, written the way an enterprise platform
 *  explains its data practices — precise, and organised by the
 *  question a business owner actually has, rather than one long
 *  paragraph of legal-sounding text. */
export default function DataUsageScreen() {
  return (
    <InfoScreen
      metaLine="Applies to every business and supplier account on TruConnect"
      paragraphs={[
        {
          heading: "What TruConnect collects",
          body: "Your account details (name, phone number, email), your business profile as you enter it, and the operational records you create — customer information, amounts owed, orders, and payment history. We collect nothing beyond what's needed to run the tools in this app.",
          icon: (c) => <Database size={16} color={c} />,
        },
        {
          heading: "Why we collect it",
          body: "Every piece of information TruConnect holds exists to power a feature you're actively using — Loan Book, Order Book, and your Business Profile all depend on it. We don't collect data speculatively for future use, and we don't collect anything unrelated to running your business.",
          icon: (c) => <ShieldCheck size={16} color={c} />,
        },
        {
          heading: "Who can see your business records",
          body: "Your customer and order records belong to you and are never visible to other businesses, suppliers, or the public on TruConnect. Staff access is limited to what's strictly necessary to operate and support the platform, and is logged and auditable.",
          icon: (c) => <Users size={16} color={c} />,
        },
        {
          heading: "How your data is protected",
          body: "Data in transit is encrypted, and your account is protected by your password together with phone verification. Access to production systems is restricted and monitored, in line with standard enterprise security practice.",
          icon: (c) => <Lock size={16} color={c} />,
        },
        {
          heading: "What we never do",
          body: "TruConnect does not sell your business or customer data, does not share it with third parties for marketing, and does not display advertising inside the app. Your records are a tool for running your business, not a product.",
          icon: (c) => <Ban size={16} color={c} />,
        },
        {
          heading: "Deletion and retention",
          body: "Records you delete are held in Trash for 7 days so mistakes can be undone, then removed. Your account data is retained for as long as your account is active, and you may request full deletion at any time — see Privacy policy for how to do that.",
          icon: (c) => <Trash2 size={16} color={c} />,
        },
      ]}
    />
  );
}
