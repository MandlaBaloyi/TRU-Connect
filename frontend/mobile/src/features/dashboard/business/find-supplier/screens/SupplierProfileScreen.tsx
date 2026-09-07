import React, { useLayoutEffect, useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Boxes, ChevronRight } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { EntityHeaderTitle } from "@/components/navigation/EntityHeaderTitle";
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
      headerRight: () => <SupplierProfileMenu onAbout={() => setInfoOpen(true)} />,
      // Social-style top bar: the supplier's own avatar + business name
      // (+ tick when verified), replacing the generic "Supplier" title.
      // Named from the ROUTE PARAM until the real profile lands, so the
      // bar never flashes the layout's generic "Supplier" first -- see
      // routes.ts's own docstring on that fix. Deliberately no onPress:
      // this screen IS the profile the header would otherwise link to.
      ...(supplier || supplierNameParam
        ? {
            headerTitle: () => (
              <EntityHeaderTitle
                name={supplier?.businessName ?? supplierNameParam ?? ""}
                subtitle="Supplier profile"
                photoUrl={supplier?.businessImageUrl ?? supplier?.photoUrl}
                verified={showsAsVerified(supplier?.verificationStatus)}
              />
            ),
          }
        : {}),
    });
  }, [navigation, supplier, supplierNameParam]);

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
      <ScrollView contentContainerStyle={styles.content}>
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

        <ProfileSection label="Products">
          <SupplierShowcase
            categories={showcase?.categories ?? []}
            isLoading={isShowcaseLoading}
            onSeeAll={(category) =>
              router.push(supplierCatalogHref(supplierId, supplier.businessName, category) as any)
            }
            onProductPress={(productId, productName) =>
              router.push(productDetailHref(supplierId, productId, productName, supplier.businessName) as any)
            }
            onAddToCart={handleAddToCart}
            addingProductId={addingProductId}
          />

          {/* THE WHOLE-CATALOGUE ENTRY POINT. Until now the only way in
              was "See all" on one arbitrary category strip -- a business
              wanting to just browse everything had to pick a category
              first, and never saw how much this supplier actually
              stocks. productCount is real (backend counts it); the row
              is hidden entirely at zero rather than offering a link to
              an empty catalogue. */}
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
        </ProfileSection>
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
