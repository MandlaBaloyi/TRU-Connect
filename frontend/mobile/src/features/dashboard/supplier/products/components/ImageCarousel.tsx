/**
 * ImageCarousel — swipeable horizontal viewer with dot indicators.
 * Deliberately shows nothing about where the images came from --
 * "Cloudinary", "media ID", "transformation" never appear here or
 * anywhere a supplier/business can see, per review: it should just
 * feel like looking at the product, not at infrastructure.
 *
 * Built now for the supplier's own product detail screen; this exact
 * component is what the business-facing product view will reuse once
 * that screen exists, rather than a second carousel being built for it.
 *
 * FALLBACK IS PER SLIDE, NOT PER CAROUSEL. A product with three photos
 * where the middle one is dead should show two photos and one category
 * tile -- not collapse the whole carousel, and certainly not leave a
 * blank page the reader assumes is a loading state. So each slide runs
 * the chain itself (CategoryImage), and the empty case is the same
 * chain with nothing to show.
 */

import React, { useState } from "react";
import { Dimensions, FlatList, StyleSheet, View } from "react-native";
import { useTheme } from "react-native-paper";

import { CategoryImage } from "@/components/categories";
import type { ProductCategory } from "@/constants/productCategories";

interface Props {
  images: string[];
  height?: number;
  /** Drives the fallback when there are no photos, or when one is
   *  broken. Optional: without it the fallback is a neutral square,
   *  which is still better than the empty space <Image> leaves. */
  category?: ProductCategory | string | null;
}

export function ImageCarousel({ images, height = 260, category }: Props) {
  const theme = useTheme();
  const [width, setWidth] = useState(Dimensions.get("window").width);
  const [activeIndex, setActiveIndex] = useState(0);

  if (images.length === 0) {
    return (
      <View
        style={[styles.placeholder, { height }]}
        onLayout={(e) => setWidth(e.nativeEvent.layout.width)}
      >
        <CategoryImage category={category} fill radius={0} />
      </View>
    );
  }

  return (
    <View onLayout={(e) => setWidth(e.nativeEvent.layout.width)}>
      <FlatList
        data={images}
        keyExtractor={(uri, index) => `${index}-${uri}`}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={(e) => {
          const index = Math.round(e.nativeEvent.contentOffset.x / width);
          setActiveIndex(index);
        }}
        renderItem={({ item }) => (
          <View style={{ width, height, backgroundColor: theme.colors.surfaceVariant }}>
            <CategoryImage
              photoUrl={item}
              category={category}
              fill
              radius={0}
            // "contain", not "cover" -- every supplier's photo has a
            // different natural shape (a tall bottle, a wide box, a
            // square item); "cover" was stretching/cropping to force
            // it to fill this box exactly, cutting parts of the photo
            // off. "contain" always shows the WHOLE photo, at its own
            // real proportions, on every device -- the same box shape
            // for everyone, never a distorted or cropped product.
              resizeMode="contain"
            />
          </View>
        )}
      />
      {images.length > 1 && (
        <View style={styles.dots}>
          {images.map((_, index) => (
            <View
              key={index}
              style={[
                styles.dot,
                {
                  backgroundColor: index === activeIndex ? theme.colors.primary : theme.colors.outline,
                },
              ]}
            />
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  placeholder: { alignItems: "center", justifyContent: "center" },
  dots: { flexDirection: "row", justifyContent: "center", gap: 6, marginTop: 8 },
  dot: { width: 6, height: 6, borderRadius: 3 },
});
