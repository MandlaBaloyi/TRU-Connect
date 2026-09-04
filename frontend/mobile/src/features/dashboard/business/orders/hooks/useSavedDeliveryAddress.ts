/**
 * useSavedDeliveryAddress -- NOT WIRED YET. The single, obvious plug-in
 * point for a real saved-address system once one exists on the
 * account/More tab: a business's own default delivery address, "check
 * your current address, enter it if you haven't, edit if it's
 * changed" -- exactly as described directly.
 *
 * Deliberately its own hook, not inline logic in
 * DeliveryPaymentScreen.tsx -- when a real backend endpoint exists,
 * this is the one function that changes; the screen itself doesn't
 * need touching. Returns null today, honestly, since there's nothing
 * real to fetch yet.
 */
export function useSavedDeliveryAddress(): { savedAddress: string | null; isLoading: boolean } {
  return { savedAddress: null, isLoading: false };
}
