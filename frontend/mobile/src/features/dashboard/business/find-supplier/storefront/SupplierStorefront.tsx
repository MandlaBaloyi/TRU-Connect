import React from "react";
import { StyleSheet, View } from "react-native";

import { Rail } from "@/features/dashboard/business/community/components/feed/Rail";
import { spacing } from "@/theme/spacing";

import { FeaturedProductBanner } from "./cards/FeaturedProductBanner";
import { SaleProductCard } from "./cards/SaleProductCard";
import { RankedProductCard } from "./cards/RankedProductCard";
import { BulkValueCard } from "./cards/BulkValueCard";
import { NewArrivalCard } from "./cards/NewArrivalCard";
import { useSupplierStorefront } from "./useSupplierStorefront";
import type { SupplierProduct } from "../types";

/** Beyond three or four, a rank stops being a recommendation and
 *  becomes trivia -- nobody chooses a product because it is the
 *  ninth most popular. */
const MAX_RANKED = 5;

/**
 * The merchandised part of a supplier's profile: their pick, what is
 * on sale, what businesses buy most, and what works out cheaper per
 * unit -- each drawn its OWN way.
 *
 * SITS ABOVE THE CATEGORY STRIPS, which SupplierShowcase still owns
 * and still draws exactly as it did. That separation is deliberate
 * rather than temporary tidiness: the strips are a catalogue (here is
 * everything, by category) and these sections are a shopfront (here is
 * what to look at first). Merging them into one contract is only worth
 * doing once these have been reviewed on a real screen.
 *
 * REUSES Rail for the headers so the section titles match the
 * Community feed exactly. Only the CARDS differ per section -- which
 * is the whole idea: same shelf, different goods.
 *
 * RENDERS NOTHING while loading. A storefront is enrichment above a
 * profile that is already complete and already useful; a row of grey
 * skeleton blocks above real content would make the page feel slower
 * than it is, for content nobody is waiting on.
 */
export function SupplierStorefront({
  supplierId,
  onProductPress,
  onAddToCart,
  addingProductId,
}: {
  supplierId: string;
  onProductPress: (productId: string, productName: string) => void;
  onAddToCart?: (product: SupplierProduct) => void;
  addingProductId?: string | null;
}) {
  const { sections, isLoading } = useSupplierStorefront(supplierId);

  if (isLoading || sections.length === 0) return null;

  return (
    <View style={styles.wrap}>
      {sections.map((section) => {
        switch (section.type) {
          case "FEATURED_PRODUCT":
            return (
              <FeaturedProductBanner
                key={section.id}
                label={section.label}
                product={section.product}
                onPress={() => onProductPress(section.product.id, section.product.name)}
                onAddToCart={onAddToCart ? () => onAddToCart(section.product) : undefined}
                isAdding={addingProductId === section.product.id}
              />
            );

          case "ON_SALE":
            return (
              <Rail
                key={section.id}
                title={section.title}
                subtitle={section.subtitle}
                data={section.products}
                keyExtractor={(product) => product.id}
                renderItem={(product) => (
                  <SaleProductCard
                    product={product}
                    onPress={() => onProductPress(product.id, product.name)}
                    onAddToCart={onAddToCart ? () => onAddToCart(product) : undefined}
                    isAdding={addingProductId === product.id}
                  />
                )}
              />
            );

          case "BEST_SELLERS":
            return (
              <Rail
                key={section.id}
                title={section.title}
                subtitle={section.subtitle}
                data={section.products.slice(0, MAX_RANKED)}
                keyExtractor={(product) => product.id}
                // A little wider than the other strips: the rank badge
                // hangs off the top-left corner of each card, and a
                // tight gap would let it overlap the card before it.
                itemGap={spacing.md}
                renderItem={(product) => (
                  <RankedProductCard
                    product={product}
                    rank={section.products.indexOf(product) + 1}
                    onPress={() => onProductPress(product.id, product.name)}
                  />
                )}
              />
            );

          case "BULK_VALUE":
            return (
              <Rail
                key={section.id}
                title={section.title}
                subtitle={section.subtitle}
                data={section.products}
                keyExtractor={(product) => product.id}
                renderItem={(product) => (
                  <BulkValueCard
                    product={product}
                    onPress={() => onProductPress(product.id, product.name)}
                  />
                )}
              />
            );

          case "NEW_ARRIVALS":
          case "CURATED":
            // ONE CARD, TWO SECTIONS. Both are image-forward strips
            // with nothing to rank or discount them by; the only
            // difference is the NEW flag, which a supplier's own
            // themed selection has no business claiming.
            return (
              <Rail
                key={section.id}
                title={section.title}
                subtitle={section.subtitle}
                data={section.products}
                keyExtractor={(product) => product.id}
                renderItem={(product) => (
                  <NewArrivalCard
                    product={product}
                    showNewFlag={section.type === "NEW_ARRIVALS"}
                    onPress={() => onProductPress(product.id, product.name)}
                  />
                )}
              />
            );

          default:
            // An unknown section from a newer server. Skipped in
            // silence -- same rule as the Community feed, and for the
            // same reason: the server must be free to ship a section
            // type before every installed build understands it.
            return null;
        }
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.lg, paddingTop: spacing.sm },
});
