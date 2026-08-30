import React, { useLayoutEffect, useState } from "react";
import { ActivityIndicator, Alert, Linking, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Heart, Mail, MessageCircle, Music2, ShoppingCart } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { ImageCarousel } from "../../../supplier/products/components";
import { calculateDiscount } from "../../../supplier/products/algorithms/discount";
import { formatCents } from "../../../supplier/products/services/productMapper";
import { CATEGORY_OPTIONS, UNIT_OPTIONS } from "../../../supplier/products/types";
import { buildWhatsAppUrl } from "../../loan-book/services/contactActions";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { palette } from "@/theme/colors";

import { useSupplierProductDetail } from "../../find-supplier/hooks/useSupplierProductDetail";
import { useRelatedProducts } from "../../find-supplier/hooks/useRelatedProducts";
import { useReportSupplier } from "../../find-supplier/hooks/useReportSupplier";
import { useAddToCart } from "../../orders/hooks/useAddToCart";
import { ApiError } from "@/services/api/apiClient";
import { ProductDetailMenu } from "../components/ProductDetailMenu";
import { ReportSupplierSheet } from "../components/ReportSupplierSheet";
import { RelatedProductsRow } from "../components/RelatedProductsRow";
import { AccordionSection } from "../components/AccordionSection";
import type { ReportReason } from "../../find-supplier/types";

const DESCRIPTION_COLLAPSED_LINES = 4;

function labelFor(options: { value: string; label: string }[], value: string): string {
  return options.find((o) => o.value === value)?.label ?? value;
}

function buildTikTokUrl(handle: string): string {
  return `https://www.tiktok.com/@${handle}`;
}

function openUrl(url: string) {
  Linking.openURL(url).catch(() => {
    // Silently ignored, same reasoning as ContactActionsRow.tsx's own
    // handlers: wa.me and tiktok.com both degrade to a normal web page
    // when the native app isn't installed, so a failure here means no
    // URL at all could be opened (no network route) -- nothing more
    // useful to do than leave the screen as it was.
  });
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
  const { supplierId, productId } = useLocalSearchParams<{ supplierId: string; productId: string }>();
  const navigation = useNavigation();
  const router = useRouter();
  const theme = useTheme();
  const { product, isLoading, isError, refetch } = useSupplierProductDetail(supplierId ?? "", productId ?? "");
  const { addToCart } = useAddToCart(supplierId ?? "");
  const { relatedProducts } = useRelatedProducts(supplierId ?? "", productId ?? "");
  const { reportSupplier, isReporting } = useReportSupplier(supplierId ?? "");

  const [descriptionExpanded, setDescriptionExpanded] = useState(false);
  const [descriptionTruncated, setDescriptionTruncated] = useState(false);
  const [reportSheetOpen, setReportSheetOpen] = useState(false);

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
      await addToCart({ productId, quantity: 1 });
      Alert.alert("Added to cart", `${product?.name ?? "This product"} was added to your cart.`, [
        { text: "Keep browsing" },
        { text: "View cart", onPress: () => router.push(`/business/orders/${supplierId}` as any) },
      ]);
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

  useLayoutEffect(() => {
    navigation.setOptions({
      title: product?.name ?? "Product",
      headerRight: () => <ProductDetailMenu onReport={() => setReportSheetOpen(true)} />,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigation, product?.name]);

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

        <View style={styles.body}>
          {/* Product details -- row-style, no arrows, always visible. */}
          <Text style={[styles.sectionHeader, { color: theme.colors.onSurface }]}>Product details</Text>
          <View style={styles.detailsList}>
            <View style={styles.detailsRow}>
              <Text style={[styles.detailsLabel, { color: theme.colors.onSurface }]}>Supplier</Text>
              <Text style={[styles.detailsValue, { color: theme.colors.onSurface }]}>{product.supplierName}</Text>
            </View>
            <View style={[styles.detailsDivider, { backgroundColor: theme.colors.outlineVariant }]} />

            <View style={styles.detailsRow}>
              <Text style={[styles.detailsLabel, { color: theme.colors.onSurface }]}>Product name</Text>
              <Text style={[styles.detailsValue, { color: theme.colors.onSurface }]}>{product.name}</Text>
            </View>
            <View style={[styles.detailsDivider, { backgroundColor: theme.colors.outlineVariant }]} />

            <View style={styles.detailsRow}>
              <Text style={[styles.detailsLabel, { color: theme.colors.onSurface }]}>Price</Text>
              <View style={styles.priceRow}>
                <Text
                  style={[styles.detailsValue, { color: discount ? theme.colors.error : theme.colors.onSurface }]}
                >
                  {formatCents(product.priceCents)}
                </Text>
                {product.compareAtPriceCents !== null && (
                  <Text style={[styles.compareAtPrice, { color: theme.colors.onSurfaceVariant }]}>
                    {formatCents(product.compareAtPriceCents)}
                  </Text>
                )}
              </View>
            </View>

            {discount && (
              <>
                <View style={[styles.detailsDivider, { backgroundColor: theme.colors.outlineVariant }]} />
                <View style={styles.detailsRow}>
                  <Text style={[styles.detailsLabel, { color: theme.colors.onSurface }]}>Discount</Text>
                  <View style={[styles.discountBadge, { backgroundColor: theme.colors.errorContainer }]}>
                    <Text style={[styles.discountBadgeText, { color: theme.colors.error }]}>
                      {discount.percentOff}% OFF
                    </Text>
                  </View>
                </View>
              </>
            )}

            <View style={[styles.detailsDivider, { backgroundColor: theme.colors.outlineVariant }]} />
            <View style={styles.detailsRow}>
              <Text style={[styles.detailsLabel, { color: theme.colors.onSurface }]}>Availability</Text>
              <View
                style={[
                  styles.availabilityBadge,
                  { backgroundColor: product.inStock ? "#E3F6EC" : theme.colors.errorContainer },
                ]}
              >
                <Text
                  style={[
                    styles.availabilityText,
                    { color: product.inStock ? palette.success : theme.colors.error },
                  ]}
                >
                  {product.inStock ? "In stock" : "Out of stock"}
                </Text>
              </View>
            </View>

            <View style={[styles.detailsDivider, { backgroundColor: theme.colors.outlineVariant }]} />
            <View style={styles.detailsRow}>
              <Text style={[styles.detailsLabel, { color: theme.colors.onSurface }]}>Sold as</Text>
              <Text style={[styles.detailsValue, { color: theme.colors.onSurface }]}>
                {labelFor(UNIT_OPTIONS, product.sellingUnit)}
              </Text>
            </View>
          </View>

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

          {/* Product Codes -- collapsible, Supplier moved up into the
              real Product details section above, so only Product code
              and Category remain here. */}
          <AccordionSection title="Product Codes">
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

          {/* Shipping/Returns -- real TRU Connect defaults, honest
              about TRU Connect not being the seller. Meant to be
              replaced once a real supplier-input form for this
              exists. */}
          <AccordionSection title="Shipping">
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

          <AccordionSection title="Returns">
            <Text style={[styles.policyText, { color: theme.colors.onSurface }]}>
              TRU Connect doesn't process returns or refunds -- that's arranged directly between you and{" "}
              {product.supplierName}.
            </Text>
            <Text style={[styles.policyText, { color: theme.colors.onSurface }]}>
              Contact {product.supplierName} directly to discuss returning or exchanging this product.
            </Text>
          </AccordionSection>

          <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />

          {/* More from [Supplier] -- ABOVE Contact. */}
          <RelatedProductsRow
            supplierName={product.supplierName}
            products={relatedProducts}
            onPressProduct={(related) =>
              router.push(`/business/my-suppliers/${supplierId}/products/${related.id}` as any)
            }
          />

          {product.contact && (
            <View style={styles.contactSection}>
              <Text style={[styles.sectionHeader, { color: theme.colors.onSurface }]}>
                Contact {product.supplierName}
              </Text>
              <View style={styles.contactActions}>
                {product.contact.whatsappNumber && (
                  <Pressable
                    onPress={() => openUrl(buildWhatsAppUrl(product.contact!.whatsappNumber!))}
                    style={({ pressed }) => [
                      styles.contactAction,
                      { backgroundColor: theme.colors.surfaceVariant },
                      pressed && styles.contactActionPressed,
                    ]}
                    accessibilityRole="button"
                    accessibilityLabel={`Message ${product.supplierName} on WhatsApp`}
                  >
                    <MessageCircle size={18} color={theme.colors.onSurface} strokeWidth={2} />
                    <Text style={[styles.contactActionLabel, { color: theme.colors.onSurface }]}>WhatsApp</Text>
                  </Pressable>
                )}
                {product.contact.tiktokHandle && (
                  <Pressable
                    onPress={() => openUrl(buildTikTokUrl(product.contact!.tiktokHandle!))}
                    style={({ pressed }) => [
                      styles.contactAction,
                      { backgroundColor: theme.colors.surfaceVariant },
                      pressed && styles.contactActionPressed,
                    ]}
                    accessibilityRole="button"
                    accessibilityLabel={`View ${product.supplierName} on TikTok`}
                  >
                    <Music2 size={18} color={theme.colors.onSurface} strokeWidth={2} />
                    <Text style={[styles.contactActionLabel, { color: theme.colors.onSurface }]}>TikTok</Text>
                  </Pressable>
                )}
                {product.contact.email && (
                  <Pressable
                    onPress={() => openUrl(`mailto:${product.contact!.email}`)}
                    style={({ pressed }) => [
                      styles.contactAction,
                      { backgroundColor: theme.colors.surfaceVariant },
                      pressed && styles.contactActionPressed,
                    ]}
                    accessibilityRole="button"
                    accessibilityLabel={`Email ${product.supplierName}`}
                  >
                    <Mail size={18} color={theme.colors.onSurface} strokeWidth={2} />
                    <Text style={[styles.contactActionLabel, { color: theme.colors.onSurface }]}>Email</Text>
                  </Pressable>
                )}
              </View>
            </View>
          )}
        </View>
      </ScrollView>

      {/* Fixed bottom bar -- price, heart, Add to Cart, always
          reachable regardless of scroll position. */}
      <View style={[styles.bottomBar, { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.outlineVariant }]}>
        <Text style={[styles.bottomBarPrice, { color: discount ? theme.colors.error : theme.colors.onSurface }]}>
          {formatCents(product.priceCents)}
        </Text>
        <Pressable
          onPress={() => Alert.alert("Coming soon", "Likes isn't available yet, but it's on the way.")}
          hitSlop={8}
          style={styles.bottomBarHeart}
          accessibilityRole="button"
          accessibilityLabel={`Like ${product.name}`}
        >
          <Heart size={24} color={theme.colors.onSurfaceVariant} strokeWidth={2.5} />
        </Pressable>
        <Pressable
          onPress={handleAddToCart}
          style={[styles.addToCartButton, { backgroundColor: theme.colors.primary }]}
          accessibilityRole="button"
          accessibilityLabel="Add to cart"
        >
          <ShoppingCart size={18} color={theme.colors.onPrimary} strokeWidth={2.2} />
          <Text style={[styles.addToCartLabel, { color: theme.colors.onPrimary }]}>Add to Cart</Text>
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
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  content: { paddingBottom: 96 },
  body: { padding: spacing.md, gap: spacing.md },
  priceRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  compareAtPrice: { ...typography.bodySmall, textDecorationLine: "line-through" },
  discountBadge: { paddingHorizontal: spacing.xs, paddingVertical: 2, borderRadius: radius.sm },
  discountBadgeText: { ...typography.caption, fontWeight: "700" },
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
  detailsRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: spacing.sm },
  detailsLabel: { ...typography.bodySmall, fontWeight: "600" },
  detailsValue: { ...typography.body, fontWeight: "700" },
  detailsDivider: { height: StyleSheet.hairlineWidth },
  contactSection: { gap: spacing.sm },
  contactActions: { flexDirection: "row", gap: spacing.sm },
  contactAction: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xs,
    minHeight: 48,
    borderRadius: radius.md,
    paddingHorizontal: spacing.sm,
  },
  contactActionPressed: { opacity: 0.7 },
  contactActionLabel: { ...typography.body, fontWeight: "600" },
  bottomBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  bottomBarPrice: { ...typography.h2, fontWeight: "700" },
  bottomBarHeart: { padding: spacing.xs },
  addToCartButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xs,
    minHeight: 48,
    borderRadius: radius.md,
  },
  addToCartLabel: { fontWeight: "700", fontSize: 15 },
});
