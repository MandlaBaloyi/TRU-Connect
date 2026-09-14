import React from "react";

import { AddressPickerField } from "@/features/dashboard/shared/location-picker/components/AddressPickerField";
import type { DeliveryLocation } from "@/features/dashboard/shared/location-picker/types";

/**
 * Where the SUPPLIER sets their own collection address.
 *
 * THE MISSING HALF OF A FEATURE THAT WAS ALREADY HALF-BUILT: the
 * collection_* columns, the business-facing "Collect from" block, and
 * the checkout screen's COLLECT branch all existed, but nothing
 * anywhere let a supplier actually enter the address — so that branch
 * could only ever say "will appear here once they've added one". This
 * is the "once".
 *
 * DELIBERATELY THE SAME TWO ENTRY POINTS AS THE BUSINESS DELIVERY
 * FLOW (DeliveryPaymentScreen): "Search address" (SearchAddressModal,
 * Mapbox geocoding) then confirm on the map, or "Choose on map"
 * (MapPickerModal) directly. Reusing those exact components rather
 * than a second address UI means one set of address semantics, one
 * geocoder, one confirm gesture — and a supplier who is also a
 * business elsewhere in the app sees the flow they already know.
 *
 * SEARCH FEEDS THE MAP, IT DOESN'T SKIP IT. A geocoded result is a
 * best guess; the supplier still confirms the exact pin, because this
 * address is what a business will actually drive to.
 *
 * NOW A WRAPPER, NOT AN IMPLEMENTATION. When the business profile
 * needed the same field, the choice was to copy this or to extract it.
 * The paragraph above argues against a second address UI, so it would
 * have been arguing against itself — the body moved to
 * location-picker/components/AddressPickerField and this keeps the
 * supplier's own wording. What remains here is the part that is
 * genuinely supplier-specific: what the thing is called out loud.
 */
export function CollectionAddressField({
  value,
  onSave,
}: {
  value: DeliveryLocation | null;
  onSave: (location: DeliveryLocation) => Promise<void>;
}) {
  return (
    <AddressPickerField
      value={value}
      onSave={onSave}
      editLabel="Edit collection address"
      searchLabel="Search address"
      searchA11yLabel="Search your address"
      mapLabel="Choose on map"
      mapA11yLabel="Choose location on map"
      pickerTitle="Collection address"
      pickerConfirmLabel="Confirm collection address"
    />
  );
}
