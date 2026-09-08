import React, { useLayoutEffect, useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Boxes, ChevronRight } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { EntityHeaderTitle } from "@/components/navigation/EntityHeaderTitle";
import { FadeIn } from "@/components/ui/FadeIn";
import { InfoHint } from "@/components/ui/InfoHint";
import { showsAsVerified } from "@/constants/config";
import { productDetailHref, supplierCatalogHref } from "../../routes";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useSupplierProfile, useRequestConnection } from "../hooks/useConnectionRequest";
import { useSupplierProfileProducts } from "../hooks/useSupplierProfileProducts";
import { useAddToCart } from "../../orders/hooks/useAddToCart";
import { ApiError } from "@/services/api/apiClient";
import type { SupplierProduct } from "../types";
import { SupplierBrandHeader } from "../components/SupplierBrandHeader";
import { SupplierShowcase } from "../components/SupplierShowcase";
import { CartButton } from "@/features/dashboard/business/community/components/header/CartButton";
import { SupplierStorefront } from "../storefront/SupplierStorefront";
import { SupplierProfileMenu } from "../components/SupplierProfileMenu";
import { SupplierConnectionInfoSheet } from "../components/SupplierConnectionInfoSheet";
import { SupplierContactRow } from "../components/SupplierContactRow";
import { SupplierTrustSignals } from "../components/SupplierTrustSignals";
import { SupplierFulfilmentBlock } from "../components/SupplierFulfilmentBlock";
import { SupplierConnectionStatus } from "../components/SupplierConnectionStatus";
import { ProfileSection, ProfileCard } from "../components/ProfileSection";

/**
 * The supplier's brand profile, seen by a business -- the conversion
 * moment (Relationship Intelligence plan, Phase 2). A brand header
 * (cover + business photo + name + "on TruConnect since ..."), a
 * category showcase of the supplier's real products with "See all in
 * <category>", then the connection CTA. The "how connecting works"
 * explainer lives behind the header ⋮ ("About connections") so the
 * screen leads with brand and products, not process copy.
 *
 * Verification shows ONLY as a tick + "Verified supplier" when the
 * supplier is genuinely verified -- never an "Unverified"/"Pending"
 * label. Browsing is open regardless of connection status; only
 * ORDERING is gated. Request Connection here still only ever produces
 * PENDING; Approve/Decline is the supplier's own screen.
 */
export default function SupplierProfileScreen() {
  const { supplierId, supplierName: supplierNameParam } = useLocalSearchParams<{
    supplierId: string;
    supplierName?: string;
  }>();
  const router = useRouter();
  const navigation = useNavigation();
  const theme = useTheme();

  const { data: supplier, isLoading, isError, refetch } = useSupplierProfile(supplierId ?? "");
  const { data: showcase, isLoading: isShowcaseLoading } = useSupplierProfileProducts(supplierId ?? "");
  const requestConnection = useRequestConnection(supplierId ?? "");

  const [infoOpen, setInfoOpen] = useState(false);
  // THE COLLAPSING HEADER. The brand header carries the supplier's
  // avatar and name at full size; the top bar stays empty until that
  // block scrolls away, and only then takes the identity over. Before
  // that, repeating the name two centimetres above itself is noise.
  //
  // A BOOLEAN, NOT THE SCROLL OFFSET. setOptions on every scroll frame
  // would rebuild the header sixty times a second; this flips at most
  // twice per scroll, and the effect below only re-runs when it does.
  const [isTitleInBar, setIsTitleInBar] = useState(false);
  // Measured, never guessed -- the brand header's height depends on
  // whether the supplier has a cover photo, a description, an activity
  // line. A hardcoded threshold would be wrong for most suppliers.
  const [brandHeaderHeight, setBrandHeaderHeight] = useState(0);
  const { addToCart } = useAddToCart(supplierId ?? "");
  // Only the card mid-request shows "Adding…", not every card at once.
  const [addingProductId, setAddingProductId] = useState<string | null>(null);

  const handleAddToCart = async (product: SupplierProduct) => {
    setAddingProductId(product.id);
    try {
      await addToCart({ productId: product.id, quantity: 1 });
    } catch (error) {
      // The backend's out-of-stock message already names the product,
      // so it's shown as-is rather than reworded.
      if (error instanceof ApiError && error.code === "OUT_OF_STOCK") {
        Alert.alert("Out of stock", error.message);
      } else {
        Alert.alert("Couldn't add to cart", "Check your connection and try again.");
      }
    } finally {
      setAddingProductId(null);
    }
  };

  useLayoutEffect(() => {
    navigation.setOptions({
      // CART AND MENU. Both fit beside the collapsing title because
      // the header's right slot is sized for exactly two icons (see
      // CommunityHeader's rightSlot) and the title beside it shrinks
      // rather than colliding. CartButton hides itself when the cart
      // is empty, so most of the time this is a single icon anyway.
      headerRight: () => (
        <View style={styles.headerActions}>
          <CartButton supplierId={supplierId ?? ""} />
          <SupplierProfileMenu onAbout={() => setInfoOpen(true)} />
        </View>
      ),
      // The identity appears ONLY once the brand header has scrolled
      // past. Until then the bar is just a back arrow and the menu --
      // see isTitleInBar above.
      ...(isTitleInBar && (supplier || supplierNameParam)
        ? {
            headerTitle: () => (
              <FadeIn>
                <EntityHeaderTitle
                  name={supplier?.businessName ?? supplierNameParam ?? ""}
                  photoUrl={supplier?.businessImageUrl ?? supplier?.photoUrl}
                  verified={showsAsVerified(supplier?.verificationStatus)}
                />
              </FadeIn>
            ),
          }
        : { headerTitle: () => null }),
    });
  }, [navigation, supplier, supplierNameParam, isTitleInBar]);

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !supplier) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load this supplier. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        // 32 rather than 16: fine enough that the swap lands where the
        // name actually leaves, coarse enough not to run the handler
        // on every frame of a flick.
        scrollEventThrottle={32}
        onScroll={(event) => {
          if (!brandHeaderHeight) return;
          // Swap once the name itself is gone, not the whole block --
          // the name sits low in the brand header, so waiting for the
          // full height would leave the bar empty well after it left.
          const threshold = brandHeaderHeight * 0.62;
          const past = event.nativeEvent.contentOffset.y > threshold;
          // Only ever sets when it actually changes, so a scroll that
          // stays on one side of the line causes no re-renders.
          setIsTitleInBar((current) => (current === past ? current : past));
        }}
      >
        <View onLayout={(event) => setBrandHeaderHeight(event.nativeEvent.layout.height)}>
          <SupplierBrandHeader
            businessName={supplier.businessName}
            category={supplier.category}
            location={supplier.location}
            verificationStatus={supplier.verificationStatus}
            memberSince={supplier.memberSince}
            description={supplier.description}
            businessImageUrl={supplier.businessImageUrl}
            coverImageUrl={supplier.coverImageUrl}
            photoUrl={supplier.photoUrl}
            activity={supplier.activity}
          />
        </View>

        {/* TRUST BEFORE PRODUCTS. An informal business deciding whether
            to send money to a supplier it has never traded with weighs
            "do other businesses buy here, and do orders go through"
            before it weighs any individual price -- so these sit
            directly under the brand header, above everything else. */}
        <SupplierTrustSignals
          businessName={supplier.businessName}
          connectedBusinessCount={supplier.connectedBusinessCount}
          trust={supplier.trust}
        />

        {/* SUPPLIER DETAILS -- where you stand with them, and how to
            reach them. One block because they answer the same
            question: "can I deal with these people, and how?" */}
        <ProfileSection
          label="Supplier details"
          accessory={
            <InfoHint
              title="Supplier details"
              body={[
                "Your connection with this supplier, and the ways they've chosen to let connected businesses contact them.",
                "Contact channels only appear once you're connected and the supplier has opted into sharing them.",
              ]}
            />
          }
        >
          <ProfileCard>
            <View style={styles.detailsBody}>
              <SupplierConnectionStatus
                status={supplier.connectionStatus}
                initiatedBy={supplier.connectionInitiatedBy}
                supplierName={supplier.businessName}
                onRequest={() => requestConnection.mutate()}
                isSubmitting={requestConnection.isPending}
              />
              {/* Renders nothing without a real channel to show. */}
              <SupplierContactRow contact={supplier.contact} />
            </View>
          </ProfileCard>
        </ProfileSection>

        <SupplierFulfilmentBlock
          offersDelivery={supplier.offersDelivery}
          minimumOrderCents={supplier.minimumOrderCents}
          address={supplier.collectionAddress}
        />

        {/* THE MERCHANDISED SECTIONS, above the category strips.
            Supplier's pick, on sale, best sellers, better-per-unit --
            each drawn its own way, because a shopfront earns attention
            by presenting different products differently, and a stack
            of identically-drawn category strips cannot say "look at
            this one first".

            Still on mock data (see useSupplierStorefront) -- every
            other block on this screen is real. It renders nothing at
            all while loading, so the profile never looks slower than
            it did. */}
        <SupplierStorefront
          supplierId={supplierId ?? ""}
          onProductPress={(productId, productName) =>
            router.push(productDetailHref(supplierId, productId, productName, supplier.businessName) as any)
          }
          onAddToCart={handleAddToCart}
          addingProductId={addingProductId}
        />

        {/* The full catalogue by category -- the "here is everything"
            half, where the storefront above is the "here is what to
            look at" half.

            NOT WRAPPED IN ProfileSection ANY MORE, and that was a real
            bug rather than a style preference. ProfileSection pads 16px
            horizontally and each strip's own list pads 16px again, so
            the strips were boxed inside a 32px inset and clipped 16px
            short of the screen edge -- they could not run off the side
            the way every other rail in the app does, which is exactly
            why they felt like they did not scroll properly. The strips
            own their own padding and now bleed to the edge like the
            storefront rails above them. */}
        <SupplierShowcase
          categories={showcase?.categories ?? []}
          isLoading={isShowcaseLoading}
          onProductPress={(productId, productName) =>
            router.push(productDetailHref(supplierId, productId, productName, supplier.businessName) as any)
          }
          onAddToCart={handleAddToCart}
          addingProductId={addingProductId}
        />

        {/* THE WHOLE-CATALOGUE ENTRY POINT, and now the ONLY one --
            the per-category "See all" links are gone (see
            SupplierShowcase). A business wanting to browse everything
            no longer has to pick a category first, and this row is
            where they see how much the supplier actually stocks.
            productCount is real (backend counts it); the row is hidden
            entirely at zero rather than offering a link to an empty
            catalogue. */}
        {supplier.productCount > 0 && (
          <Pressable
            onPress={() => router.push(supplierCatalogHref(supplierId, supplier.businessName) as any)}
            style={({ pressed }) => [
              styles.shopAll,
              {
                backgroundColor: theme.colors.surface,
                borderColor: theme.colors.outlineVariant,
                opacity: pressed ? 0.85 : 1,
              },
            ]}
            accessibilityRole="button"
            accessibilityLabel={`Shop all ${supplier.productCount} products`}
          >
            <Boxes size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            <Text style={[styles.shopAllLabel, { color: theme.colors.onSurface }]}>
              Shop all {supplier.productCount} {supplier.productCount === 1 ? "product" : "products"}
            </Text>
            <ChevronRight size={18} color={theme.colors.onSurfaceVariant} />
          </Pressable>
        )}
      </ScrollView>

      <SupplierConnectionInfoSheet
        visible={infoOpen}
        supplierName={supplier.businessName}
        onClose={() => setInfoOpen(false)}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  headerActions: { flexDirection: "row", alignItems: "center", gap: 2 },
  content: { paddingBottom: spacing.xxl },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  detailsBody: { padding: spacing.md, gap: spacing.md },
  shopAll: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
  },
  shopAllLabel: { ...typography.body, fontWeight: "700", flex: 1 },
});
