import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Card, IconButton, Text } from 'react-native-paper';
import type { Product } from '../types';
import { ProductStatusBadge } from './ProductStatusBadge';
import { formatPrice } from '../services/pricingCalculator';

interface Props {
  product: Product;
  onPress: (product: Product) => void;
  onEdit: (product: Product) => void;
  onToggleAvailability: (product: Product) => void;
}

/** Mirrors Document 03 \u00a74.3 ProductManagementCard. */
export function ProductCard({ product, onPress, onEdit, onToggleAvailability }: Props) {
  const thumbnail = product.images[0]?.imageUrl;

  return (
    <Card style={styles.card} onPress={() => onPress(product)}>
      <View style={styles.row}>
        {thumbnail ? (
          <Card.Cover source={{ uri: thumbnail }} style={styles.thumbnail} />
        ) : (
          <View style={[styles.thumbnail, styles.thumbnailPlaceholder]} />
        )}
        <Card.Content style={styles.content}>
          <Text variant="titleMedium" numberOfLines={1}>
            {product.name}
          </Text>
          <Text variant="bodyMedium" style={styles.price}>
            {formatPrice(product.price)} / {product.unit}
          </Text>
          <ProductStatusBadge product={product} />
        </Card.Content>
        <View style={styles.actions}>
          <IconButton icon="pencil-outline" onPress={() => onEdit(product)} accessibilityLabel="Edit product" />
          <IconButton
            icon="cube-outline"
            onPress={() => onToggleAvailability(product)}
            accessibilityLabel="Update stock status"
          />
        </View>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: { marginBottom: 12 },
  row: { flexDirection: 'row', alignItems: 'center', padding: 8 },
  thumbnail: { width: 64, height: 64, borderRadius: 8 },
  thumbnailPlaceholder: { backgroundColor: '#eee' },
  content: { flex: 1, marginLeft: 12, gap: 4 },
  price: { opacity: 0.8 },
  actions: { flexDirection: 'column' },
});
