import React, { useLayoutEffect, useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Heart, ShoppingCart } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { productDetailHref } from "../../routes";
import { EntityHeaderTitle } from "@/components/navigation/EntityHeaderTitle";
import { ErrorState } from "@/components/feedback/ErrorState";
import { ImageCarousel } from "../../../supplier/products/components";
import { calculateDiscount } from "../../../supplier/products/algorithms/discount";
import { formatCents } from "../../../supplier/products/services/productMapper";
import { CATEGORY_OPTIONS } from "../../../supplier/products/types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { palette } from "@/theme/colors";

import { useSupplierProductDetail } from "../../find-supplier/hooks/useSupplierProductDetail";
import { useRelatedProducts } from "../../find-supplier/hooks/useRelatedProducts";
import { useReportSupplier } from "../../find-supplier/hooks/useReportSupplier";
import { useAddToCart } from "../../orders/hooks/useAddToCart";
import { useCart } from "../../orders/hooks/useCart";
import { ApiError } from "@/services/api/apiClient";
import { ProductDetailMenu } from "../components/ProductDetailMenu";
import { ReportSupplierSheet } from "../components/ReportSupplierSheet";
import { RelatedProductsRow } from "../components/RelatedProductsRow";
import { AccordionSection } from "@/components/ui/AccordionSection";
import { ProductBuyBlock } from "../components/ProductBuyBlock";
import { ProductFulfilmentNote } from "../components/ProductFulfilmentNote";
import { SupplierContactRow } from "../../find-supplier/components/SupplierContactRow";
import { ProfileCard } from "../../find-supplier/components/ProfileSection";
import { QuantityStepper } from "@/components/ui/QuantityStepper";
import type { ReportReason, SupplierProduct } from "../../find-supplier/types";

const DESCRIPTION_COLLAPSED_LINES = 4;

function labelFor(options: { value: string; label: string }[], value: string): string {
  return options.find((o) => o.value === value)?.label ?? value;
}

/**
 * A business's own read-only view of ONE product from a connected (or
 * merely browsable) supplier's catalogue.
 *
 * STRUCTURE, confirmed directly before building:
 *
 * 1. "Product details" -- row-style (label left, value right, thin
 *    dividers), NO accordion arrows, always visible. Supplier, Product
 *    name, Price, Discount (its own row, not crammed into the price
 *    row), Availability, Sold as -- the real decision-making
 *    information a business needs immediately, not something to tuck
 *    away.
 * 2. Description -- its own block right below Product details, same
 *    Read More behaviour as before.
 * 3. "Product Codes" (renamed from what used to be "Product details"
 *    -- Supplier moved up into the real Product details section
 *    above, so this now only holds Product code + Category) --
 *    collapsible, defaults open.
 * 4. "Shipping" and "Returns" -- collapsible, default open, real
 *    TRU Connect copy. TRU Connect isn't a seller or an e-commerce
 *    platform -- it provides the ecosystem/technology connecting
 *    businesses and suppliers, so this copy is honest about that: a
 *    default explaining delivery/returns happen directly with the
 *    supplier, not a fabricated policy TRU Connect doesn't actually
 *    have. Meant to be replaced once a real supplier-input form for
 *    this exists.
 * 5. "More from [Supplier]" -- ABOVE Contact, not below (moved after
 *    direct feedback).
 * 6. "Contact [Supplier]" -- now the last thing before the fixed
 *    bottom bar.
 *
 * THE FIXED BOTTOM BAR (price, heart, Add to Cart) is the real start
 * of ordering -- Add to Cart is "Coming soon" for this pass, but the
 * handler is a single, clean swap-point (handleAddToCart below) for
 * when a real cart exists.
 *
 * THE 3-DOT MENU ("Report this product") reuses the SAME underlying
 * report mechanism as the catalogue's own "Report".
 *
 * THE SCREEN TITLE IS THE PRODUCT'S OWN NAME, not the static word
 * "Product" -- so navigating deep through "More from [Supplier]"
 * always shows visual confirmation of which product you're on.
 */
export default function SupplierProductDetailScreen() {
  const { supplierId, productId, productName: productNameParam, supplierName: supplierNameParam } =
    useLocalSearchParams<{
      supplierId: string;
      productId: string;
      productName?: string;
      supplierName?: string;
    }>();
  const navigation = useNavigation();
  const router = useRouter();
  const theme = useTheme();
  const { product, isLoading, isError, refetch } = useSupplierProductDetail(supplierId ?? "", productId ?? "");
  const { addToCart } = useAddToCart(supplierId ?? "");
  // Needed for the minimum-order shortfall: it's measured against the
  // WHOLE cart, not this product alone -- see ProductFulfilmentNote.
  const { cart } = useCart(supplierId ?? "");
  const { relatedProducts } = useRelatedProducts(supplierId ?? "", productId ?? "");
  const { reportSupplier, isReporting } = useReportSupplier(supplierId ?? "");

  const [descriptionExpanded, setDescriptionExpanded] = useState(false);
  const [descriptionTruncated, setDescriptionTruncated] = useState(false);
  const [reportSheetOpen, setReportSheetOpen] = useState(false);
  // Resets to 1 on every product, deliberately -- carrying a quantity
  // across products would silently add 10 of something you looked at
  // after ordering 10 of something else.
  const [quantity, setQuantity] = useState(1);
  // Separate from `quantity` above: the related row adds ONE of a
  // DIFFERENT product, and must not borrow the quantity chosen for the
  // product currently on screen.
  const [addingRelatedId, setAddingRelatedId] = useState<string | null>(null);

  const handleAddRelated = async (related: SupplierProduct) => {
    setAddingRelatedId(related.id);
    try {
      await addToCart({ productId: related.id, quantity: 1 });
    } catch (error) {
      if (error instanceof ApiError && error.code === "OUT_OF_STOCK") {
        Alert.alert("Out of stock", error.message);
      } else {
        Alert.alert("Couldn't add to cart", "Check your connection and try again.");
      }
    } finally {
      setAddingRelatedId(null);
    }
  };

  const handleReport = async (reason: ReportReason, details: string | null) => {
    try {
      await reportSupplier({ reason, details, productId: productId ?? undefined });
      setReportSheetOpen(false);
      Alert.alert("Report submitted", "Thanks for letting us know. Our team will review this.");
    } catch {
      Alert.alert("Couldn't submit report", "Check your connection and try again.");
    }
  };

  const handleAddToCart = async () => {
    if (!supplierId || !productId) return;
    try {
      await addToCart({ productId, quantity });
      Alert.alert(
        "Added to cart",
        `${quantity} × ${product?.name ?? "this product"} added to your cart.`,
        [
          { text: "Keep browsing" },
          { text: "View cart", onPress: () => router.push(`/business/orders/${supplierId}` as any) },
        ]
      );
    } catch (error) {
      // Real, specific message when the product is out of stock --
      // a real bug found after direct report: this check never
      // existed at all before. The backend's own message already
      // names the exact product, so it's shown as-is.
      if (error instanceof ApiError && error.code === "OUT_OF_STOCK") {
        Alert.alert("Out of stock", error.message);
        return;
      }
      Alert.alert("Couldn't add to cart", "Check your connection and try again.");
    }
  };

  // Both halves prefer the fetched value and fall back to the route
  // param the caller already had -- see business/routes.ts's own
  // docstring on the header-flash fix.
  const headerSupplierName = product?.supplierName ?? supplierNameParam ?? null;
  const headerProductName = product?.name ?? productNameParam ?? null;

  useLayoutEffect(() => {
    navigation.setOptions({
      title: headerProductName ?? "Product",
      // SAME SOCIAL TOP BAR AS THE CATALOGUE AND CART, per direct
      // product feedback: the identity line is always the SUPPLIER
      // (avatar + business name) and the second line says which screen
      // of theirs you're on -- "Stock catalogue", "Cart", "Supplier
      // profile", or here the product's own name. Showing the product
      // name alone meant a business three taps deep had nothing on
      // screen confirming whose product they were looking at.
      ...(headerSupplierName
        ? {
            headerTitle: () => (
              <EntityHeaderTitle
                name={headerSupplierName}
                subtitle={headerProductName ?? undefined}
                photoUrl={product?.supplierBusinessImageUrl}
              />
            ),
          }
        : {}),
      headerRight: () => <ProductDetailMenu onReport={() => setReportSheetOpen(true)} />,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigation, headerSupplierName, headerProductName, product?.supplierBusinessImageUrl]);

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !product) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load this product. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const discount = calculateDiscount(product.priceCents, product.compareAtPriceCents);

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <ImageCarousel images={product.images} />

        {/* THE BUY BLOCK replaces a six-row label/value table -- see
            ProductBuyBlock's own docstring for what that table got
            wrong and which questions this answers instead. Supplier
            and product name aren't repeated here: both are already in
            the top bar. */}
        <ProductBuyBlock product={product} />

        {/* Moves with the quantity stepper below, so pressing + visibly
            closes the gap to the minimum -- a blocker turned into an
            instruction. */}
        <ProductFulfilmentNote
          offersDelivery={product.supplierOffersDelivery}
          minimumOrderCents={product.supplierMinimumOrderCents}
          cartTotalCents={cart?.totalCents ?? 0}
          lineTotalCents={product.priceCents * quantity}
        />

        <View style={styles.body}>
          {/* Description -- its own block right below Product
              details, not a row inside it. */}
          {product.description && (
            <View style={styles.field}>
              <Text style={[styles.sectionHeader, { color: theme.colors.onSurface }]}>Description</Text>
              <View style={styles.measurer} pointerEvents="none">
                <Text
                  style={[styles.value, styles.descriptionText, { color: theme.colors.onSurface }]}
                  onTextLayout={(event) => {
                    if (event.nativeEvent.lines.length > DESCRIPTION_COLLAPSED_LINES) {
                      setDescriptionTruncated(true);
                    }
                  }}
                >
                  {product.description}
                </Text>
              </View>
              <Text
                style={[styles.value, styles.descriptionText, { color: theme.colors.onSurface }]}
                numberOfLines={descriptionExpanded ? undefined : DESCRIPTION_COLLAPSED_LINES}
              >
                {product.description}
              </Text>
              {descriptionTruncated && (
                <Pressable
                  onPress={() => setDescriptionExpanded((prev) => !prev)}
                  accessibilityRole="button"
                  accessibilityLabel={descriptionExpanded ? "Show less" : "Read more"}
                >
                  <Text style={[styles.readMore, { color: theme.colors.primary }]}>
                    {descriptionExpanded ? "Show less" : "Read more"}
                  </Text>
                </Pressable>
              )}
            </View>
          )}

          <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />

          {/* Shipping and Returns come BEFORE Product Codes: how it
              reaches you and what happens if it's wrong are decisions;
              a product code is a reference you look up. All three start
              collapsed -- reference material you open on a question,
              not something to re-read every visit. Each is separated by
              a rule so a stack of closed headers doesn't read as one
              undifferentiated list. */}
          <AccordionSection title="Shipping" defaultExpanded={false}>
            <Text style={[styles.policyText, { color: theme.colors.onSurface }]}>
              TRU Connect provides the technology connecting you with suppliers -- we don't handle delivery
              ourselves. Delivery is arranged directly with {product.supplierName}.
            </Text>
            <Text style={[styles.policyText, { color: theme.colors.onSurface }]}>
              Contact {product.supplierName} using the details below to confirm delivery options, timing, and any
              costs.
            </Text>
          </AccordionSection>

          <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />

          <AccordionSection title="Returns" defaultExpanded={false}>
            <Text style={[styles.policyText, { color: theme.colors.onSurface }]}>
              TRU Connect doesn't process returns or refunds -- that's arranged directly between you and{" "}
              {product.supplierName}.
            </Text>
            <Text style={[styles.policyText, { color: theme.colors.onSurface }]}>
              Contact {product.supplierName} directly to discuss returning or exchanging this product.
            </Text>
          </AccordionSection>

          <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />

          <AccordionSection title="Product Codes" defaultExpanded={false}>
            <View style={styles.detailsRow}>
              <Text style={[styles.detailsLabel, { color: theme.colors.onSurface }]}>Product code</Text>
              <Text style={[styles.detailsValue, { color: theme.colors.onSurface }]}>{product.productCode}</Text>
            </View>
            <View style={[styles.detailsDivider, { backgroundColor: theme.colors.outlineVariant }]} />
            <View style={styles.detailsRow}>
              <Text style={[styles.detailsLabel, { color: theme.colors.onSurface }]}>Category</Text>
              <Text style={[styles.detailsValue, { color: theme.colors.onSurface }]}>
                {labelFor(CATEGORY_OPTIONS, product.category)}
              </Text>
            </View>
          </AccordionSection>

          <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />

          {/* More from [Supplier] -- ABOVE Contact. */}
          <RelatedProductsRow
            supplierName={product.supplierName}
            products={relatedProducts}
            onPressProduct={(related) =>
              router.push(productDetailHref(supplierId, related.id, related.name, headerSupplierName) as any)
            }
            onAddToCart={handleAddRelated}
            addingProductId={addingRelatedId}
          />

          <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />

          {/* SAME CARD AS THE SUPPLIER PROFILE. This screen had its own
              hand-rolled copy of the WhatsApp/TikTok/Email buttons,
              styled slightly differently -- so the same three actions
              looked like two different features depending on which
              screen you reached them from. SupplierContactRow is the
              one implementation now; find-supplier is the feature
              my-suppliers already depends on, so importing it points
              the arrow the right way. */}
          {product.contact && (
            <View style={styles.contactBlock}>
              {/* The screen's OWN section header, not ProfileSection's
                  tiny uppercase label. That label works for a short,
                  fixed word like "TRACK RECORD"; set in caps with wide
                  letter-spacing, "CONTACT MACMAN BUSINESSES" became a
                  long shouted string that read as less important than
                  the sections around it, which use this heading. Within
                  one screen, matching that screen beats matching a
                  different one. */}
              <Text style={[styles.sectionHeader, { color: theme.colors.onSurface }]}>
                Contact {product.supplierName}
              </Text>
              <ProfileCard>
                <View style={styles.contactCardBody}>
                  <SupplierContactRow contact={product.contact} />
                </View>
              </ProfileCard>
            </View>
          )}
        </View>
      </ScrollView>

      {/* Fixed bottom bar -- price, heart, Add to Cart, always
          reachable regardless of scroll position. */}
      {/* THE BUY BAR. Two rows now, not one: the quantity has to sit
          beside the action it applies to, and cramming a stepper into
          the single row alongside price + heart + button left nothing
          room to breathe on a narrow phone.

          THE LINE TOTAL, not the unit price, is what the top row shows
          once quantity > 1 -- "R200.00" while you're about to add three
          cases answers the wrong question. The unit price stays
          visible beneath it so the arithmetic is checkable. */}
      <View style={[styles.bottomBar, { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.outlineVariant }]}>
        <View style={styles.bottomBarTop}>
          <View style={styles.bottomBarPriceBlock}>
            <Text style={[styles.bottomBarPrice, { color: theme.colors.onSurface }]}>
              {formatCents(product.priceCents * quantity)}
            </Text>
            {quantity > 1 && (
              <Text style={[styles.bottomBarUnit, { color: theme.colors.onSurfaceVariant }]}>
                {formatCents(product.priceCents)} each
              </Text>
            )}
          </View>
          <QuantityStepper value={quantity} onChange={setQuantity} disabled={!product.inStock} />
          <Pressable
            onPress={() => Alert.alert("Coming soon", "Likes isn't available yet, but it's on the way.")}
            hitSlop={8}
            style={styles.bottomBarHeart}
            accessibilityRole="button"
            accessibilityLabel={`Like ${product.name}`}
          >
            <Heart size={24} color={theme.colors.onSurfaceVariant} strokeWidth={2.5} />
          </Pressable>
        </View>
        <Pressable
          onPress={handleAddToCart}
          disabled={!product.inStock}
          style={[
            styles.addToCartButton,
            {
              backgroundColor: product.inStock ? theme.colors.primary : theme.colors.surfaceVariant,
            },
          ]}
          accessibilityRole="button"
          accessibilityLabel={product.inStock ? "Add to cart" : "Out of stock"}
          accessibilityState={{ disabled: !product.inStock }}
        >
          <ShoppingCart
            size={18}
            color={product.inStock ? theme.colors.onPrimary : theme.colors.onSurfaceVariant}
            strokeWidth={2.2}
          />
          <Text
            style={[
              styles.addToCartLabel,
              { color: product.inStock ? theme.colors.onPrimary : theme.colors.onSurfaceVariant },
            ]}
          >
            {product.inStock ? "Add to Cart" : "Out of stock"}
          </Text>
        </Pressable>
      </View>

      <ReportSupplierSheet
        visible={reportSheetOpen}
        supplierName={product.supplierName}
        isSubmitting={isReporting}
        onSubmit={handleReport}
        onClose={() => setReportSheetOpen(false)}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  contactBlock: { gap: spacing.sm },
  contactCardBody: { padding: spacing.md },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  content: { paddingBottom: 96 },
  body: { padding: spacing.md, gap: spacing.md },
  priceRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  compareAtPrice: { ...typography.bodySmall, textDecorationLine: "line-through" },
  availabilityBadge: { paddingHorizontal: spacing.sm, paddingVertical: 4, borderRadius: radius.pill },
  availabilityText: { ...typography.bodySmall, fontWeight: "700" },
  divider: { height: StyleSheet.hairlineWidth },
  field: { gap: 4 },
  label: { ...typography.bodySmall, fontWeight: "600" },
  value: { ...typography.body, fontWeight: "600" },
  sectionHeader: { ...typography.body, fontWeight: "700", marginBottom: 2 },
  descriptionText: { ...typography.body, fontWeight: "400" },
  measurer: { height: 0, overflow: "hidden" },
  readMore: { ...typography.bodySmall, fontWeight: "700", marginTop: 4 },
  policyText: { ...typography.body, lineHeight: 20 },
  detailsList: { gap: 0 },
  // REAL BUG, visible on a real device: this was space-between with no
  // width constraint on either child, so a long value (a product name
  // that ran to two lines) simply expanded until it overlapped its own
  // label. Every row was exposed; the name just triggered it first.
  //
  // The label now holds a fixed share and stops shrinking, and the
  // value takes the rest and wraps inside it. alignItems moved to
  // flex-start so a wrapped, multi-line value stays top-aligned with
  // its label instead of drifting to the vertical middle of the row.
  detailsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: spacing.md,
    paddingVertical: spacing.sm,
  },
  detailsLabel: { ...typography.bodySmall, fontWeight: "600", flexShrink: 0, maxWidth: "40%" },
  detailsValue: { ...typography.body, fontWeight: "700", flex: 1, textAlign: "right" },
  detailsDivider: { height: StyleSheet.hairlineWidth },
  // Stacks now (was a single row): price+quantity+heart on top, the
  // full-width action beneath. A wide Add to Cart is also a bigger,
  // easier target than one squeezed beside three other controls.
  bottomBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  bottomBarTop: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  bottomBarPriceBlock: { flex: 1 },
  bottomBarPrice: { ...typography.h2, fontWeight: "700" },
  bottomBarUnit: { ...typography.bodySmall, fontSize: 11 },
  bottomBarHeart: { padding: spacing.xs },
  addToCartButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xs,
    minHeight: 48,
    borderRadius: radius.md,
  },
  addToCartLabel: { fontWeight: "700", fontSize: 15 },
});
