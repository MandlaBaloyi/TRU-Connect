import React from "react";
import { WifiOff, RefreshCw, ShieldCheck } from "lucide-react-native";
import { InfoScreen } from "@/features/dashboard/business/settings/components/InfoScreen";

/**
 * INFORMATIONAL, not a toggle. Offline-first is an ARCHITECTURAL
 * capability of TruConnect, not a feature the user switches on and
 * off — presenting it as a switch would misrepresent how the app
 * actually works.
 */
export default function OfflineModeScreen() {
  return (
    <InfoScreen
      statusLabel="Offline-ready"
      paragraphs={[
        {
          heading: "Your business doesn't stop for a bad signal",
          body: "TruConnect keeps working when your connection drops. Record a sale, log a payment, or update an order the same way you always do — nothing about how the app works changes because you're offline.",
          icon: (c) => <WifiOff size={16} color={c} />,
        },
        {
          heading: "Everything catches up automatically",
          body: "Once your device reconnects, everything you recorded while offline syncs on its own. You don't need to press anything or remember to \"go back online\" — it just happens in the background.",
          icon: (c) => <RefreshCw size={16} color={c} />,
        },
        {
          heading: "Why this isn't a switch",
          body: "Working offline is built into how TruConnect is designed, not a feature you turn on. There's nothing to configure here — it's simply always on, so your business records are never at the mercy of your signal.",
          icon: (c) => <ShieldCheck size={16} color={c} />,
        },
      ]}
    />
  );
}
