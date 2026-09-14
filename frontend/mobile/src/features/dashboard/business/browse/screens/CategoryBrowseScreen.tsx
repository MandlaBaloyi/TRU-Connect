import React, { useLayoutEffect } from "react";
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { CategoryIcon } from "@/components/categories";
import { ErrorState } from "@/components/feedback/ErrorState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { categoryLabel } from "@/constants/productCategories";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { BrowseProductCard } from "../components/BrowseProductCard";
import { useCategoryBrowse } from "../hooks/useCategoryBrowse";

/**
 * Where a category chip finally lands.
 *
 * IT USED TO GO TO SUPPLIER SEARCH. Tapping "Drinks" found SHOPS, not
 * drinks -- and for a business that has just installed the app, the
 * chips are the ONLY section of the Community tab that works at all.
 * So the first thing a new user did was the thing that worked least.
 *
 * STOCK ACROSS EVERY VISIBLE SUPPLIER, which is only possible because
 * browsing was opened at the platform level (V2_00 2.3): the connection
 * is the supplier's optional gate on ORDERING, never on seeing.
 *
 * THE EMPTY STATE IS HONEST AND SPECIFIC. "No drinks yet" names the
 * category and says nobody is selling it rather than implying the
 * shopper did something wrong -- and on a young platform with a thin
 * catalogue it is a state people will genuinely hit.
 */
export default function CategoryBrowseScreen() {
  const { category } = useLocalSearchParams<{ category?: string }>();
  const theme = useTheme();
  const router = useRouter();
  const navigation = useNavigation();

  const label = category ? categoryLabel(category) : "Browse";
  const { products, isLoading, isError, refetch } = useCategoryBrowse(category);

  useLayoutEffect(() => {
    navigation.setOptions({ title: label });
  }, [navigation, label]);

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Could not load this category." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <FlatList
        data={products}
        keyExtractor={(product) => product.id}
        numColumns={2}
        columnWrapperStyle={styles.row}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => (
          <BrowseProductCard
            product={item}
            // Straight to the product on ITS supplier's shopfront --
            // the screen that already knows how to show one product,
            // rather than a second product detail built for this list.
            onPress={() =>
              router.push(
                `/business/my-suppliers/${item.supplierId}/products/${item.id}` as any,
              )
            }
          />
        )}
        ListEmptyComponent={
          <View style={styles.centre}>
            <CategoryIcon
              category={category ?? "OTHER"}
              size={40}
              color={theme.colors.onSurfaceVariant}
            />
            <Text style={[styles.emptyTitle, { color: theme.colors.onSurface }]}>
              No {label.toLowerCase()} yet
            </Text>
            <Text style={[styles.emptyBody, { color: theme.colors.onSurfaceVariant }]}>
              Nobody is selling in this category right now. Try another one, or invite a
              supplier you already buy from.
            </Text>
          </View>
        }
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, gap: spacing.md },
  row: { gap: spacing.md },
  centre: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    paddingTop: spacing.xxl,
    paddingHorizontal: spacing.lg,
  },
  emptyTitle: { ...typography.h2, textAlign: "center" },
  emptyBody: { ...typography.body, textAlign: "center" },
});
