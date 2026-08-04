/**
 * useShareReceipt — captures LoanReceiptCard as an image and hands it to
 * the OS share sheet via expo-sharing.
 *
 * WHY expo-sharing, NOT React Native's built-in Share API: RN's `Share`
 * module is built for sharing TEXT and URLs. On Android specifically, its
 * `message`/`url` fields do not reliably open a proper "share this image"
 * sheet for a local file:// path — passed a file path, Android's Share
 * intent typically just shares the path as plain text, which silently
 * fails the whole point of this feature. `expo-sharing`'s `shareAsync()`
 * is purpose-built for exactly this — "share this local file via the OS
 * share sheet" — and is the Expo-idiomatic choice for a managed-workflow
 * project like this one.
 *
 * WHY THE OFF-SCREEN RENDER-THEN-CAPTURE DANCE: react-native-view-shot
 * needs a real, laid-out, mounted View to capture — it cannot render a
 * component invisibly on demand. So the flow is:
 *   1. Caller calls `shareReceipt(loan, customer, ownerFirstName)`.
 *   2. This hook stores that as `pendingReceipt` state.
 *   3. LoanDetailsScreen renders <LoanReceiptCard> off-screen (position
 *      absolute, far off the visible viewport — NOT display:none, which
 *      some capture backends fail to rasterize) whenever
 *      `pendingReceipt` is set, forwarding `receiptRef`.
 *   4. Once mounted, this hook captures it, shares it, then clears
 *      `pendingReceipt` so the off-screen node unmounts again.
 *
 * A short delay after setting pendingReceipt (one requestAnimationFrame)
 * gives React time to actually commit and lay out the off-screen view
 * before capture runs — capturing on the same tick the state is set
 * risks capturing a not-yet-painted (blank) view.
 */

import { useCallback, useRef, useState } from "react";
import { View } from "react-native";
import { captureRef } from "react-native-view-shot";
import * as Sharing from "expo-sharing";

import type { Customer, LoanEntryView } from "../types";
import type { ReceiptData } from "../services/receiptService";
import { buildReceiptData } from "../services/receiptService";

export function useShareReceipt() {
  const receiptRef = useRef<View>(null);
  const [pendingReceipt, setPendingReceipt] = useState<ReceiptData | null>(null);
  const [isSharing, setIsSharing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const shareReceipt = useCallback(
    async (loan: LoanEntryView, customer: Customer, ownerFirstName?: string) => {
      setError(null);
      setIsSharing(true);
      const data = buildReceiptData(loan, customer, ownerFirstName);
      setPendingReceipt(data);

      // Let the off-screen view actually mount and lay out before capturing.
      await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));

      try {
        if (!receiptRef.current) {
          throw new Error("Receipt could not be prepared.");
        }

        const isSharingAvailable = await Sharing.isAvailableAsync();
        if (!isSharingAvailable) {
          throw new Error("Sharing isn't available on this device.");
        }

        const uri = await captureRef(receiptRef, { format: "png", quality: 1 });
        await Sharing.shareAsync(uri, {
          mimeType: "image/png",
          dialogTitle: `Credit sale record for ${customer.name}`,
        });
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Could not create the receipt. Try again."
        );
      } finally {
        setPendingReceipt(null);
        setIsSharing(false);
      }
    },
    []
  );

  return { shareReceipt, pendingReceipt, receiptRef, isSharing, error };
}
