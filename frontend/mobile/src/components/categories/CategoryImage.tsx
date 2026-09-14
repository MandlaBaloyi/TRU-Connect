import React from "react";
import { Image, StyleSheet, View } from "react-native";
import { ImageOff } from "lucide-react-native";

import { CategoryTile } from "./CategoryTile";
import type { ProductCategory } from "@/constants/productCategories";
import { palette } from "@/theme/colors";

/**
 * A product's picture, or the best thing available instead.
 *
 * THE FALLBACK CHAIN, in order:
 *
 *   1  the product photograph, when there is one and it loads
 *   2  the category tile, when there is no photograph OR the
 *      photograph fails to load
 *   3  a neutral placeholder, only when we do not even know the
 *      category
 *
 * STEP 2's SECOND HALF IS THE WHOLE POINT. Before this component, a
 * missing photograph and a BROKEN one behaved differently: the first
 * showed a category-less blank and the second showed nothing at all,
 * because <Image> with a dead URI renders empty space and says nothing.
 * Cloudinary assets get deleted, moderation rejects them, URLs expire —
 * a broken image is not a rare case, and "silently blank" is the worst
 * possible way to render it. onError is what turns a branch into a
 * chain.
 *
 * ONE COMPONENT SO THERE IS ONE BEHAVIOUR. Every screen that showed a
 * product used to decide this for itself, which is why the empty states
 * disagreed with each other. If a screen wants a different look it
 * should pass a size, not write its own fallback.
 */
export function CategoryImage({
  photoUrl,
  category,
  size = 56,
  radius = 8,
  fill = false,
  resizeMode,
}: {
  photoUrl?: string | null;
  category?: ProductCategory | string | null;
  size?: number;
  radius?: number;
  /** Fill the parent instead of taking a fixed square. For cards that
   *  already own a sized wrapper with badges positioned over it. */
  fill?: boolean;
  resizeMode?: "cover" | "contain";
}) {
  const [failed, setFailed] = React.useState(false);

  // A new URL deserves a fresh attempt -- without this, one broken
  // image in a recycled list row poisons every product scrolled into
  // that row afterwards.
  React.useEffect(() => setFailed(false), [photoUrl]);

  const box = fill
    ? ({ width: "100%", height: "100%" } as const)
    : ({ width: size, height: size, borderRadius: radius } as const);
  // When filling, the glyph is sized off the parent rather than `size`,
  // which is unknown -- a fixed fraction of a known square is the only
  // thing available, so fall back to a sensible constant.
  const glyph = fill ? 28 : Math.round(size * 0.36);

  if (photoUrl && !failed) {
    return (
      <Image
        source={{ uri: photoUrl }}
        style={box}
        resizeMode={resizeMode}
        onError={() => setFailed(true)}
      />
    );
  }

  if (category) {
    return <CategoryTile category={category} size={size} radius={radius} fill={fill} />;
  }

  return (
    <View style={[styles.blank, box, { backgroundColor: palette.neutral500 }]}>
      <ImageOff size={glyph} color={palette.white} strokeWidth={1.6} />
    </View>
  );
}

const styles = StyleSheet.create({
  blank: { alignItems: "center", justifyContent: "center" },
});
