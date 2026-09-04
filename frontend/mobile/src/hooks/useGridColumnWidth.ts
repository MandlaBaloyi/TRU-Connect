import { useWindowDimensions } from "react-native";

/**
 * THE REAL FIX for a genuine, confirmed bug -- percentage widths
 * (e.g. "31%") never account for `gap` in React Native's own flexbox
 * implementation, so 3 tiles at 31% width plus 2 real gaps between
 * them can genuinely overflow the container on typical screen sizes.
 * Confirmed directly: a real screenshot showed exactly this --
 * 2-per-row instead of the intended 3, on a grid using the old
 * percentage-only approach.
 *
 * This computes the exact PIXEL width per tile from the real screen
 * width, subtracting the container's own horizontal padding and every
 * gap between columns first -- the only approach that's genuinely
 * reliable across device sizes, not just "happens to fit" on one.
 */
export function useGridColumnWidth(columns: number, containerPaddingPx: number, gapPx: number): number {
  const { width: screenWidth } = useWindowDimensions();
  const totalGaps = (columns - 1) * gapPx;
  const availableWidth = screenWidth - containerPaddingPx * 2 - totalGaps;
  return availableWidth / columns;
}
