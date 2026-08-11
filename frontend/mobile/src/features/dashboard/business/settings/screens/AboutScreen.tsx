import React from "react";
import Constants from "expo-constants";
import { Target, Wallet, ClipboardList, Store, Users, Compass, Heart } from "lucide-react-native";
import { InfoScreen } from "@/features/dashboard/business/settings/components/InfoScreen";

/** REAL static content. */
export default function AboutScreen() {
  return (
    <InfoScreen
      metaLine={`Version ${Constants.expoConfig?.version ?? "1.0.0"}`}
      paragraphs={[
        {
          heading: "What TruConnect is",
          body: "Business infrastructure for the South African informal economy — built so a spaza shop, trader, or small business can run their daily operations from one place, on the phone they already carry.",
          icon: (c) => <Target size={16} color={c} />,
        },
        {
          heading: "Loan Book",
          body: "Keeps track of what customers owe you and every payment they make against it, so you always know exactly where you stand without relying on memory or a paper notebook.",
          icon: (c) => <Wallet size={16} color={c} />,
        },
        {
          heading: "Order Book",
          body: "Keeps track of orders customers place with you, from the moment they're placed through to completion, along with your daily revenue as it comes in.",
          icon: (c) => <ClipboardList size={16} color={c} />,
        },
        {
          heading: "My Business",
          body: "Your business's profile on TruConnect — what you sell, where you trade, and how customers and suppliers can reach you.",
          icon: (c) => <Store size={16} color={c} />,
        },
        {
          heading: "Where TruConnect is going",
          body: "TruConnect is being built to connect businesses with their suppliers directly, and over time to support the wider network of relationships a business depends on — one product, built for both sides of that relationship.",
          icon: (c) => <Compass size={16} color={c} />,
        },
        {
          heading: "Community",
          body: "TruConnect is being built alongside the businesses that use it. If something isn't working the way it should, Report a problem under Help & support goes straight to the people building it.",
          icon: (c) => <Users size={16} color={c} />,
        },
        {
          heading: "Powered by TruePoint",
          body: "TruConnect is built and operated by TruePoint.",
          icon: (c) => <Heart size={16} color={c} />,
        },
      ]}
    />
  );
}
