import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import {
  exploreHref,
  productDetailHref,
  supplierCatalogHref,
  supplierProfileHref,
} from "../../../routes";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { Rail } from "./Rail";
import { SupplierCard } from "../cards/SupplierCard";
import { SponsoredSupplierCard } from "../cards/SponsoredSupplierCard";
import { SupplierAvatarTile } from "../cards/SupplierAvatarTile";
import { ProductTile } from "../cards/ProductTile";
import { PromoCard } from "../cards/PromoCard";
import { CategoryChipRow } from "../chips/CategoryChipRow";
import { ExploreKindsCard } from "./ExploreKindsCard";
import type { FeedSection } from "../../types";
import type { FeedTap } from "../../services/impressionService";

/**
 * Renders ONE feed section, whatever kind it is. The screen above
 * knows only that it has a list of sections; this is the only file
 * that knows what each type looks like.
 *
 * THIS IS THE SECOND OF TWO GATES, NOT THE ONLY ONE. useCommunityFeed's
 * isWorthRendering() runs first and drops unknown types before they
 * ever reach this switch -- so adding a case HERE and nowhere else
 * produces a section that is sent by the server, renderable by this
 * file, and invisible, with no error to follow. That is exactly how
 * EXPLORE_KINDS shipped broken.
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
export function FeedSectionView({
  section,
  onTap,
}: {
  section: FeedSection;
  /** REPORTED BEFORE NAVIGATING, never after. The next line unmounts
   *  this screen, and a callback scheduled behind a navigation is a
   *  callback that sometimes does not run -- which would silently lose
   *  taps on exactly the cards that worked. The buffer itself lives one
   *  level up in CommunityFeed, so leaving does not lose it. */
  onTap?: (tap: FeedTap) => void;
}) {
  const router = useRouter();
  const theme = useTheme();

  const openSupplier = (id: string, name: string, position: number) => {
    onTap?.({
      rail: section.id,
      position,
      itemId: id,
      itemType: "SUPPLIER",
      // A SUPPLIER CARD *IS* THE SUPPLIER, so the id serves as both the
      // thing looked at and the party who would be billed for it.
      supplierId: id,
    });
    router.push(supplierProfileHref(id, name) as any);
  };

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
          onSelect={(category, index) => {
            onTap?.({
              rail: section.id,
              position: index,
              itemId: category.value,
              itemType: "CATEGORY",
            });
            router.push(`/business/browse/${encodeURIComponent(category.value)}` as any);
          }}
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
          subtitle={section.subtitle}
          data={section.suppliers}
          keyExtractor={(supplier) => supplier.id}
          itemGap={spacing.md}
          onSeeAll={seeAll}
          renderItem={(supplier, index) => (
            <SupplierAvatarTile
              supplier={supplier}
              onPress={() => openSupplier(supplier.id, supplier.businessName, index)}
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
          renderItem={(supplier, index) => (
            <SupplierCard
              supplier={supplier}
              onPress={() => openSupplier(supplier.id, supplier.businessName, index)}
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
          renderItem={(product, index) => (
            <ProductTile
              product={product}
              onPress={() => {
                onTap?.({
                  rail: section.id,
                  position: index,
                  itemId: product.id,
                  itemType: "PRODUCT",
                  supplierId: product.supplierId,
                });
                router.push(
                  productDetailHref(
                    product.supplierId,
                    product.id,
                    product.name,
                    product.supplierName
                  ) as any
                );
              }}
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
      //
      // THE CARD IS ITS OWN COMPONENT NOW. This used to stretch a
      // SupplierCard to SUPPLIER_CARD_WIDTH + PRODUCT_TILE_WIDTH, and a
      // 240px rail tile does not become a banner by being told it is
      // wider -- its cover band became a large empty rectangle. See
      // SponsoredSupplierCard for the shape that replaced it.
      return (
        <View style={styles.sponsored}>
          <Text style={[styles.sponsoredLabel, { color: theme.colors.onSurfaceVariant }]}>
            {section.label}
          </Text>
          {section.subtitle ? (
            <Text
              style={[styles.sponsoredSubtitle, { color: theme.colors.onSurfaceVariant }]}
            >
              {section.subtitle}
            </Text>
          ) : null}
          <SponsoredSupplierCard
            supplier={section.supplier}
            onPress={() => openSupplier(section.supplier.id, section.supplier.businessName, 0)}
          />
        </View>
      );

    case "EXPLORE_KINDS":
      // THE ONLY SECTION THAT LEAVES THE FEED, and the server puts it
      // last for that reason -- see business_sections.explore_kinds.
      // Everything above this point is a supplier the shop has some
      // claim on; this is the way to the ones it has none on.
      return (
        <ExploreKindsCard
          title={section.title}
          subtitle={section.subtitle}
          kinds={section.kinds}
          onSelect={(kind) => router.push(exploreHref(kind) as any)}
        />
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
  // NOT UPPERCASE AND NOT BOLD, so it reads as a caption under the
  // disclosure rather than competing with it. The word "Sponsored"
  // stays the loudest thing in this block -- that is a rule about
  // disclosure, not about hierarchy.
  sponsoredSubtitle: { ...typography.caption, marginTop: -2 },
});
