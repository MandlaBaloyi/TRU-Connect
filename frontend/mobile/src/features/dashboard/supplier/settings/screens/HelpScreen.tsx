import React from "react";
import { BookOpen, Package, Boxes, ClipboardList, Users } from "lucide-react-native";
import { InfoScreen } from "@/features/dashboard/shared/settings/components/InfoScreen";
import { SUPPORT_CONTACTS } from "@/features/dashboard/shared/settings/supportContacts";

/**
 * REAL contact methods + real static guidance — supplier side.
 *
 * The business Help screen (business/settings/screens/HelpScreen.tsx)
 * explains Loan Book, Order Book and Trash. None of those exist on
 * this side, so this is a sibling rather than a shared screen; the
 * contacts, which ARE identical, come from
 * shared/settings/supportContacts.tsx.
 *
 * EVERY DESTINATION NAMED BELOW IS ONE THAT ACTUALLY EXISTS TODAY —
 * Products, Inventory and Stock Orders under Account; Community for
 * connections. Nothing here points at a screen that has not been
 * built, which is the same rule the COMING_SOON entries elsewhere in
 * Settings follow from the other direction.
 */
export default function SupplierHelpScreen() {
  return (
    <InfoScreen
      contacts={SUPPORT_CONTACTS}
      paragraphs={[
        {
          heading: "Getting started",
          body: "Products, Inventory and Stock Orders all live under the Account tab. Products is what businesses see and buy from, Inventory is what you actually have, and Stock Orders is where orders from businesses arrive for you to accept or decline.",
          icon: (c) => <BookOpen size={16} color={c} />,
        },
        {
          heading: "Products basics",
          body: "Add a product with a price, a unit, and photos, and it becomes part of the catalogue businesses browse. Products you mark unavailable stay in your list but stop showing to businesses — you never have to delete something just to take it off sale for a while.",
          icon: (c) => <Package size={16} color={c} />,
        },
        {
          heading: "Inventory basics",
          body: "Inventory tracks the stock behind your products, so what a business sees in your catalogue reflects what you can actually supply. Bulk Products, also under Account, is the faster way to add or update many products at once.",
          icon: (c) => <Boxes size={16} color={c} />,
        },
        {
          heading: "Handling stock orders",
          body: "When a business places an order it arrives in Stock Orders as pending. Accepting it confirms you can supply it; declining it frees the business to order elsewhere. Your delivery terms and minimum order value are set on your supplier profile and are applied at checkout automatically.",
          icon: (c) => <ClipboardList size={16} color={c} />,
        },
        {
          heading: "Your connections",
          body: "The Community tab is where businesses connect with you and where you invite businesses of your own. A business must be connected before it can see your catalogue or place an order, so your connection list is effectively your customer list.",
          icon: (c) => <Users size={16} color={c} />,
        },
      ]}
    />
  );
}
