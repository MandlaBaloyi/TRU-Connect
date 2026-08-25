/**
 * Text sanitizers -- small, reusable input-cleaning helpers. Kept
 * separate from any one screen (matching discount.ts/unitPricing.ts's
 * own precedent in this folder) since more than one field wants the
 * same treatment: ProductForm's own name and SKU inputs today, bulk
 * import's row validator a natural next place to reuse this.
 */

/**
 * Strips emoji from typed text, applied as the user types (not just
 * validated after the fact) -- REAL BUG FOUND DURING REVIEW: a
 * product's own name and SKU had no filtering at all, so a keyboard's
 * emoji picker could produce a SKU that was literally just two emoji
 * and nothing else -- useless as a tracking label, the entire point
 * SKU exists for. Description is DELIBERATELY NOT run through this --
 * casual, descriptive text is exactly where emoji read as natural
 * ("🐱 nice smell for evening"), unlike a name or a tracking code
 * meant to stay clean and unambiguous.
 *
 * Covers the main emoji Unicode blocks (emoticons, misc symbols and
 * pictographs, transport, supplemental symbols, dingbats), skin-tone
 * modifiers, the zero-width joiner used to combine multi-part emoji,
 * variation selectors, and flag/regional-indicator pairs. Not
 * byte-for-byte exhaustive against every emoji Unicode has ever
 * defined, but covers what a real keyboard's emoji picker actually
 * produces.
 */
const EMOJI_PATTERN =
  /[\u{1F1E6}-\u{1F1FF}\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2190}-\u{21FF}\u{2B00}-\u{2BFF}\u{FE00}-\u{FE0F}\u{200D}]/gu;

export function stripEmoji(text: string): string {
  return text.replace(EMOJI_PATTERN, "");
}
