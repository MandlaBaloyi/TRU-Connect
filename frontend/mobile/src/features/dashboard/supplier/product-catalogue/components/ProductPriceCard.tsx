import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text } from 'react-native-paper';
import type { Product } from '../types';
import { formatPrice, sortTiersByQuantity } from '../services/pricingCalculator';

interface Props {
  product: Pick<Product, 'price' | 'unit' | 'bulkPricingRules'>;
}

export function ProductPriceCard({ product }: Props) {
  const tiers = sortTiersByQuantity(product.bulkPricingRules ?? []);

  return (
    <View style={styles.container}>
      <Text variant="headlineSmall" style={styles.price}>
        {formatPrice(product.price)}
        <Text variant="bodyMedium"> / {product.unit}</Text>
      </Text>

      {tiers.length > 0 && (
        <View style={styles.tiers}>
          <Text variant="labelMedium" style={styles.tiersTitle}>
            Bulk Pricing
          </Text>
          {tiers.map((tier) => (
            <View key={tier.id} style={styles.tierRow}>
              <Text variant="bodySmall">
                {tier.minQuantity}+ {product.unit}
              </Text>
              <Text variant="bodySmall">
                {formatPrice(tier.price)} / {product.unit}
              </Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { paddingVertical: 8 },
  price: { fontWeight: '700' },
  tiers: { marginTop: 12, gap: 4 },
  tiersTitle: { marginBottom: 4, opacity: 0.7 },
  tierRow: { flexDirection: 'row', justifyContent: 'space-between' },
});
