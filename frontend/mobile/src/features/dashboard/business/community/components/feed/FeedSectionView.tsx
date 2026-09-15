import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { productDetailHref, supplierCatalogHref, supplierProfileHref } from "../../../routes";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { Rail } from "./Rail";
import { SupplierCard, SUPPLIER_CARD_WIDTH } from "../cards/SupplierCard";
import { SupplierAvatarTile } from "../cards/SupplierAvatarTile";
import { ProductTile, PRODUCT_TILE_WIDTH } from "../cards/ProductTile";
import { PromoCard } from "../cards/PromoCard";
import { CategoryChipRow } from "../chips/CategoryChipRow";
import type { FeedSection } from "../../types";

/**
 * Renders ONE feed section, whatever kind it is. The screen above
 * knows only that it has a list of sections; this is the only file
 * that knows what each type looks like.
 *
 * THE DEFAULT CASE RETURNS NULL, AND THAT IS THE MOST IMPORTANT LINE
 * IN THIS FILE. A server that has shipped a new section type must not
 * be able to crash an older build -- otherwise the feed is only ever
 * as flexible as the oldest app in the wild, and every commercial
 * request becomes a release. Unknown sections are skipped in silence.
 *
 * NAVIGATION IS DECIDED HERE, not carried in the payload. The cards
 * are dumb; where a tap goes is the app's business. The route helpers
 * also carry the supplier's name through as a param, which is what
 * keeps the destination's own header correct on its first frame (see
 * business/routes.ts on the header-flash fix).
 */
export function FeedSectionView({ section }: { section: FeedSection }) {
  const router = useRouter();
  const theme = useTheme();

  const openSupplier = (id: string, name: string) =>
    router.push(supplierProfileHref(id, name) as any);

  // ONE PLACE DECIDES WHETHER A RAIL HAS A CHEVRON, so a new rail
  // cannot accidentally ship without one -- or with one that leads
  // nowhere. Rail itself only renders the affordance when this is
  // non-null, which is why undefined is the right "no" rather than a
  // handler that does nothing.
  const seeAll =
    section.hasMore && section.seeAllHref
      ? () => router.push(section.seeAllHref as any)
      : undefined;

  switch (section.type) {
    case "CATEGORY_CHIPS":
      return (
        <CategoryChipRow
          categories={section.categories}
          // IT FINDS STOCK NOW, NOT SHOPS. This routed to supplier
          // search until the catalogue-wide browse existed -- so
          // tapping "Drinks" returned a list of wholesalers, and for a
          // new business the chips are the only section of this tab
          // that works at all. The first thing they did was the thing
          // that worked least.
          onSelect={(category) =>
            router.push(`/business/browse/${encodeURIComponent(category.value)}` as any)
          }
        />
      );

    case "SUPPLIER_AVATARS":
      // ONE ROW. A two-row version was built and rejected on sight:
      // it fits twelve avatars in the width that holds six, and it
      // reads as a contact grid rather than as a shelf -- which is the
      // wrong shape for a rail whose neighbours are all single rows.
      // Density was never the problem this screen had.
      return (
        <Rail
          title={section.title}
          data={section.suppliers}
          keyExtractor={(supplier) => supplier.id}
          itemGap={spacing.md}
          onSeeAll={seeAll}
          renderItem={(supplier) => (
            <SupplierAvatarTile
              supplier={supplier}
              onPress={() => openSupplier(supplier.id, supplier.businessName)}
            />
          )}
        />
      );

    case "SUPPLIER_RAIL":
      return (
        <Rail
          title={section.title}
          subtitle={section.subtitle}
          onSeeAll={seeAll}
          data={section.suppliers}
          keyExtractor={(supplier) => supplier.id}
          renderItem={(supplier) => (
            <SupplierCard
              supplier={supplier}
              onPress={() => openSupplier(supplier.id, supplier.businessName)}
            />
          )}
        />
      );

    case "PRODUCT_RAIL":
      return (
        <Rail
          title={section.title}
          subtitle={section.subtitle}
          onSeeAll={seeAll}
          data={section.products}
          keyExtractor={(product) => product.id}
          renderItem={(product) => (
            <ProductTile
              product={product}
              onPress={() =>
                router.push(
                  productDetailHref(
                    product.supplierId,
                    product.id,
                    product.name,
                    product.supplierName
                  ) as any
                )
              }
            />
          )}
        />
      );

    case "PROMO":
      return <PromoCard promo={section.promo} onPress={(href) => router.push(href as any)} />;

    case "SPONSORED_SUPPLIER":
      // LABELLED, ALWAYS AND VISIBLY. Paid placement that reads as an
      // organic recommendation is the fastest way to lose the trust
      // this whole platform is built on -- and disclosure is not
      // optional under advertising rules either. The label comes from
      // the server so the exact wording can follow whatever those
      // rules end up requiring, but the app never renders this section
      // without one.
      return (
        <View style={styles.sponsored}>
          <Text style={[styles.sponsoredLabel, { color: theme.colors.onSurfaceVariant }]}>
            {section.label}
          </Text>
          <View
            style={[
              styles.sponsoredCard,
              { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant },
            ]}
          >
            <SupplierCard
              supplier={section.supplier}
              width={SUPPLIER_CARD_WIDTH + PRODUCT_TILE_WIDTH - spacing.md}
              onPress={() => openSupplier(section.supplier.id, section.supplier.businessName)}
            />
          </View>
        </View>
      );

    default:
      return null;
  }
}

const styles = StyleSheet.create({
  sponsored: { paddingHorizontal: spacing.md, gap: spacing.xs },
  sponsoredLabel: {
    ...typography.caption,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.6,
  },
  sponsoredCard: { padding: spacing.sm, borderRadius: radius.lg, borderWidth: 1 },
});
